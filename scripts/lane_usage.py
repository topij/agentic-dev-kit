#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Rank headless lanes by the tokens and cost they recorded (read-only).

Two sources, kept apart because neither is known to contain the other:

* **result** — what `launch_lane.py` already wrote into each terminal receipt:
  `terminal.usage` for the launch round plus every `terminal.resumes[].usage`. These
  are the runtime's own figures from Claude's `--output-format json` result object.
  A Codex lane records `usage: null` there, so it has no result row.
* **subagents** — the per-subagent transcripts Claude Code writes beside the parent
  session, `<projects-root>/<project>/<session-id>/subagents/*.jsonl`, each message
  carrying its own `usage` block. The session ids come from the receipt (the launch
  round's result object and each resume entry), so no project-slug guess is needed.
  The transcript layout is a harness artifact, not a documented interface: a missing
  or unreadable one is reported, never treated as zero.

Whether the result object's `usage` already counts subagent spend is the runtime's
definition, which this does not check, so the two are never added together.

**Tokens, not dollars, from transcripts.** No price table lives here: prices are
external facts that rot in a repository, and a lane run under a subscription has a
shadow price, not an invoice. `total_cost_usd` is shown only where the runtime itself
reported it.

**Best-effort by contract.** It reads, never writes, and a malformed receipt or
transcript becomes an explicit note on its row. Exit 0 unless `--strict` is passed
and no lane had any usage, or the sessions directory cannot be found (exit 2).

Usage:
    uv run <engine-dir>/lane_usage.py                  # every lane, ranked
    uv run <engine-dir>/lane_usage.py --since 2026-11-01 --json
    uv run <engine-dir>/lane_usage.py --sessions-dir <dir> --rank-by subagent-tokens
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

TOKEN_FIELDS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)
RANK_KEYS = ("result-tokens", "subagent-tokens", "cost")


def _empty_tokens() -> dict[str, int]:
    return dict.fromkeys(TOKEN_FIELDS, 0)


def _int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _finite(value: object) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _read_json(path: Path) -> Any:
    """Parse one JSON file, or None when it is absent, unreadable or not JSON."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, RecursionError):
        return None


def _canonical_session_id(value: object) -> str | None:
    """A session id only when it is a canonical UUID: it becomes a path component."""
    if not isinstance(value, str):
        return None
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        return None
    return value if str(parsed) == value else None


def _launch_session_id(final_message_path: object) -> str | None:
    """The `session_id` of the launch round's Claude JSON result, if it has one."""
    if not isinstance(final_message_path, str) or not final_message_path:
        return None
    value = _read_json(Path(final_message_path))
    if not isinstance(value, dict) or value.get("type") != "result":
        return None
    return _canonical_session_id(value.get("session_id"))


def _utc(stamp: object) -> dt.datetime | None:
    """An aware UTC instant, or None. A naive stamp has no knowable instant."""
    if not isinstance(stamp, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


# --- result-object source -------------------------------------------------------


def result_usage(terminal: dict[str, Any]) -> dict[str, Any]:
    """Sum the runtime-reported usage over the launch round and every resume round.

    Returns `{"available": False, "reason": ...}` when no round carried figures,
    never a zero row, so a lane with no record cannot read as a free one.
    """
    rounds: list[tuple[str, object]] = [("launch", terminal.get("usage"))]
    resumes = terminal.get("resumes")
    if isinstance(resumes, list):
        for entry in resumes:
            if isinstance(entry, dict):
                rounds.append((f"resume-{entry.get('round')}", entry.get("usage")))

    tokens = _empty_tokens()
    cost: float | int | None = None
    models: set[str] = set()
    counted: list[str] = []
    missing: list[str] = []
    for name, usage in rounds:
        if not isinstance(usage, dict):
            missing.append(name)
            continue
        counted.append(name)
        figures = usage.get("usage")
        if isinstance(figures, dict):
            for field in TOKEN_FIELDS:
                tokens[field] += _int(figures.get(field)) or 0
        round_cost = _finite(usage.get("total_cost_usd"))
        if round_cost is not None:
            cost = round_cost if cost is None else cost + round_cost
        round_models = usage.get("models")
        if isinstance(round_models, dict):
            models.update(str(m) for m in round_models)

    if not counted:
        return {"available": False, "reason": "no round recorded runtime usage"}
    result: dict[str, Any] = {
        "available": True,
        "tokens": tokens,
        "total_tokens": sum(tokens.values()),
        "total_cost_usd": cost,
        "models": sorted(models),
        "rounds_counted": counted,
    }
    if missing:
        result["rounds_without_usage"] = missing
    return result


# --- subagent-transcript source --------------------------------------------------


def _iter_records(path: Path):
    """Parsed records of a .jsonl transcript; an unparseable line is skipped."""
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (ValueError, RecursionError):
                    continue
                if isinstance(record, dict):
                    yield record
    except (OSError, UnicodeDecodeError):
        return


def summarize_agent(transcript: Path) -> dict[str, Any]:
    """Total one subagent transcript's per-message usage."""
    tokens = _empty_tokens()
    models: set[str] = set()
    messages = 0
    for record in _iter_records(transcript):
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        messages += 1
        model = message.get("model")
        if isinstance(model, str):
            models.add(model)
        for field in TOKEN_FIELDS:
            tokens[field] += _int(usage.get(field)) or 0
    meta = _read_json(transcript.with_name(f"{transcript.stem}.meta.json"))
    description = meta.get("description") if isinstance(meta, dict) else None
    return {
        "agent_id": transcript.stem,
        "description": description if isinstance(description, str) else None,
        "models": sorted(models),
        "assistant_messages": messages,
        "tokens": tokens,
    }


def _session_dirs(projects_root: Path, session_id: str) -> list[Path]:
    """Every `<project>/<session_id>` directory under the transcript root.

    Session ids are UUIDs, so one match is the expected case; a guarded listing
    keeps a pruned or unreadable root a no-data result rather than a crash.
    """
    found: list[Path] = []
    try:
        projects = sorted(p for p in projects_root.iterdir() if p.is_dir())
    except OSError:
        return found
    for project in projects:
        candidate = project / session_id
        try:
            if candidate.is_dir():
                found.append(candidate)
        except OSError:
            continue
    return found


def subagent_usage(projects_root: Path, session_ids: list[str]) -> dict[str, Any]:
    """Sum the subagent transcripts of every session the lane ran under."""
    if not session_ids:
        return {"available": False, "reason": "receipt names no Claude session id"}
    agents: list[dict[str, Any]] = []
    located: list[str] = []
    for session_id in session_ids:
        dirs = _session_dirs(projects_root, session_id)
        if dirs:
            located.append(session_id)
        for session_dir in dirs:
            try:
                paths = sorted((session_dir / "subagents").glob("*.jsonl"))
            except OSError:
                continue
            agents.extend(summarize_agent(p) for p in paths)
    if not located:
        return {
            "available": False,
            "reason": f"no transcript directory for the lane's session under {projects_root}",
        }
    tokens = _empty_tokens()
    for agent in agents:
        for field in TOKEN_FIELDS:
            tokens[field] += agent["tokens"][field]
    return {
        # A located session with no subagents/ directory is a real zero: the
        # transcript exists and the lane dispatched nothing.
        "available": True,
        "agent_count": len(agents),
        "tokens": tokens,
        "total_tokens": sum(tokens.values()),
        "agents": sorted(agents, key=lambda a: -sum(a["tokens"].values())),
    }


# --- receipts --------------------------------------------------------------------


def lane_row(receipt_path: Path, projects_root: Path) -> dict[str, Any]:
    """One lane's row from its terminal receipt."""
    row: dict[str, Any] = {
        "scope": receipt_path.parent.name,
        "receipt": str(receipt_path),
    }
    receipt = _read_json(receipt_path)
    if not isinstance(receipt, dict):
        row["note"] = "receipt is unreadable or not a JSON object"
        row["result"] = {"available": False, "reason": "unreadable receipt"}
        row["subagents"] = {"available": False, "reason": "unreadable receipt"}
        return _with_flat_fields(row)
    request = receipt.get("request") if isinstance(receipt.get("request"), dict) else {}
    compute = request.get("compute") if isinstance(request.get("compute"), dict) else {}
    row.update(
        {
            "descriptor_id": receipt.get("descriptor_id"),
            "status": receipt.get("status"),
            "runtime": request.get("runtime"),
            "tier": compute.get("tier"),
            "model": compute.get("model"),
        }
    )
    terminal = receipt.get("terminal")
    if not isinstance(terminal, dict):
        reason = "receipt has no terminal record (lane still running or never finished)"
        row["result"] = {"available": False, "reason": reason}
        row["subagents"] = {"available": False, "reason": reason}
        return _with_flat_fields(row)
    row["finished_at"] = terminal.get("finished_at")
    row["lane_state"] = terminal.get("lane_state")
    row["result"] = result_usage(terminal)
    if row["runtime"] == "codex" and not row["result"]["available"]:
        row["result"]["reason"] = "codex's final-text transport carries no usage figures"

    session_ids: list[str] = []
    launch_id = _launch_session_id(terminal.get("final_message_path"))
    if launch_id:
        session_ids.append(launch_id)
    resumes = terminal.get("resumes")
    for entry in resumes if isinstance(resumes, list) else []:
        sid = _canonical_session_id(entry.get("session_id")) if isinstance(entry, dict) else None
        if sid and sid not in session_ids:
            session_ids.append(sid)
    row["session_ids"] = session_ids
    row["subagents"] = subagent_usage(projects_root, session_ids)
    return _with_flat_fields(row)


def _with_flat_fields(row: dict[str, Any]) -> dict[str, Any]:
    """Copy the headline figures to the top of the row for a budget or queue reader.

    `tokens` and `cost_usd` are the runtime's own figures (the result source);
    `subagent_tokens` is the transcript sum, kept separate for the reason the module
    docstring gives. Each is None when its source is unavailable, never 0.
    """
    result, subagents = row["result"], row["subagents"]
    row["tokens"] = result.get("total_tokens") if result.get("available") else None
    row["cost_usd"] = result.get("total_cost_usd") if result.get("available") else None
    row["subagent_tokens"] = (
        subagents.get("total_tokens") if subagents.get("available") else None
    )
    return row


def _receipts(sessions_dir: Path) -> list[Path]:
    try:
        return sorted(sessions_dir.glob("*/launch-receipt-*.json"))
    except OSError:
        return []


def _rank_value(row: dict[str, Any], rank_by: str) -> float:
    if rank_by == "subagent-tokens":
        value = row["subagents"].get("total_tokens")
    elif rank_by == "cost":
        value = row["result"].get("total_cost_usd")
    else:
        value = row["result"].get("total_tokens")
    return float(value) if isinstance(value, (int, float)) else -1.0


def build_report(
    sessions_dir: Path,
    projects_root: Path,
    *,
    since: dt.date | None = None,
    rank_by: str = "result-tokens",
) -> dict[str, Any]:
    rows = [lane_row(path, projects_root) for path in _receipts(sessions_dir)]
    if since is not None:
        floor = dt.datetime.combine(since, dt.time(), tzinfo=dt.timezone.utc)
        kept = []
        for row in rows:
            finished = _utc(row.get("finished_at"))
            # A lane with no finish instant cannot be placed in the window; it is
            # kept so the report shows it rather than silently shortening the list.
            if finished is None or finished >= floor:
                kept.append(row)
        rows = kept
    rows.sort(key=lambda r: (-_rank_value(r, rank_by), r["scope"]))
    return {
        "sessions_dir": str(sessions_dir),
        "projects_root": str(projects_root),
        "since": since.isoformat() if since else None,
        "rank_by": rank_by,
        "lanes": rows,
        "lanes_without_usage": [
            r["scope"]
            for r in rows
            if not r["result"]["available"] and not r["subagents"]["available"]
        ],
    }


# --- CLI -------------------------------------------------------------------------


def _default_sessions_dir(cwd: Path) -> Path | None:
    """`$DEVKIT_SESSIONS_DIR`, else the sibling `dev-model-sessions` of the primary
    checkout — the same default `dev_session.sh` resolves (`scripts/lib/repo_root.sh`).
    """
    override = os.environ.get("DEVKIT_SESSIONS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    try:
        listing = subprocess.run(
            ["git", "-C", str(cwd), "worktree", "list", "--porcelain", "-z"],
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    first = listing.split(b"\0", 1)[0]
    if not first.startswith(b"worktree "):
        return None
    primary = Path(os.fsdecode(first[len(b"worktree "):]))
    if not primary.is_absolute() or not (primary / ".git").exists():
        return None
    return primary.parent / "dev-model-sessions"


def _format_tokens(source: dict[str, Any]) -> str:
    if not source.get("available"):
        return "—"
    return f"{source['total_tokens']:,}"


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"lane usage — {report['sessions_dir']} (ranked by {report['rank_by']})",
        "result tokens are the runtime's own report; subagent tokens are summed from "
        "transcripts and may overlap them, so the columns are never added",
        "",
        f"{'scope':<28} {'status':<10} {'model':<10} {'result tok':>14} {'cost usd':>9} "
        f"{'subagent tok':>14}",
    ]
    for row in report["lanes"]:
        cost = row["result"].get("total_cost_usd")
        lines.append(
            f"{row['scope'][:28]:<28} {str(row.get('status'))[:10]:<10} "
            f"{str(row.get('model'))[:10]:<10} {_format_tokens(row['result']):>14} "
            f"{(f'{cost:.4f}' if isinstance(cost, (int, float)) else '—'):>9} "
            f"{_format_tokens(row['subagents']):>14}"
        )
    if not report["lanes"]:
        lines.append("(no launch receipts found)")
    missing = report["lanes_without_usage"]
    if missing:
        lines.append("")
        lines.append("no usage recorded from either source:")
        for row in report["lanes"]:
            if row["scope"] in missing:
                lines.append(f"  {row['scope']}: {row['result'].get('reason')}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--sessions-dir", help="lane sessions directory (default: dev_session.sh's)")
    parser.add_argument(
        "--projects-root",
        default=os.environ.get("CLAUDE_PROJECTS_DIR") or str(Path.home() / ".claude" / "projects"),
        help="root holding Claude Code's per-project transcript directories",
    )
    parser.add_argument("--since", help="only lanes that finished on or after this ISO date")
    parser.add_argument("--rank-by", choices=RANK_KEYS, default="result-tokens")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--strict", action="store_true", help="exit 1 when no lane had usage from either source"
    )
    args = parser.parse_args(argv)

    since = None
    if args.since:
        try:
            since = dt.date.fromisoformat(args.since)
        except ValueError:
            print(f"error: --since is not an ISO date: {args.since!r}", file=sys.stderr)
            return 2

    if args.sessions_dir:
        sessions_dir = Path(args.sessions_dir).expanduser().resolve()
    else:
        found = _default_sessions_dir(Path.cwd())
        if found is None:
            print(
                "error: cannot resolve the sessions directory; pass --sessions-dir "
                "or set DEVKIT_SESSIONS_DIR",
                file=sys.stderr,
            )
            return 2
        sessions_dir = found

    report = build_report(
        sessions_dir,
        Path(args.projects_root).expanduser(),
        since=since,
        rank_by=args.rank_by,
    )
    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_text(report))
    any_usage = any(
        r["result"]["available"] or r["subagents"]["available"] for r in report["lanes"]
    )
    return 1 if args.strict and not any_usage else 0


if __name__ == "__main__":
    sys.exit(main())
