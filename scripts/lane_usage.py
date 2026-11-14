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
  or unreadable one is reported, never treated as zero. The records Claude Code
  writes per content block of one response are counted once.

Whether the result object's `usage` already counts subagent spend is the runtime's
definition, which this does not check, so the two are never added together.

**Tokens, not dollars, from transcripts.** No price table lives here: prices are
external facts that rot in a repository, and a lane run under a subscription has a
shadow price, not an invoice. `total_cost_usd` is shown only where the runtime itself
reported it.

**Best-effort by contract.** It reads, never writes, and a malformed receipt or
transcript becomes an explicit note on its row. Exit 0 unless `--strict` is passed
and no lane had any usage; exit 2 when the sessions directory cannot be resolved
or does not exist, or `--since` is not a date.

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
    """A non-negative int, or None: a negative token count is not a measurement."""
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


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
    invalid: list[str] = []
    for name, usage in rounds:
        if not isinstance(usage, dict):
            missing.append(name)
            continue
        figures = usage.get("usage")
        figures = figures if isinstance(figures, dict) else {}
        reported = [field for field in TOKEN_FIELDS if field in figures]
        valid = {f: _int(figures[f]) for f in reported if _int(figures[f]) is not None}
        round_cost = _finite(usage.get("total_cost_usd"))
        if round_cost is not None and round_cost < 0:
            round_cost = None
        if len(valid) != len(reported) or (
            usage.get("total_cost_usd") is not None and round_cost is None
        ):
            # A field the runtime reported but that is not a non-negative number
            # makes the round's figures untrustworthy, so none of them count.
            invalid.append(name)
            continue
        if not valid and round_cost is None:
            # An empty usage object says nothing; counting it would read as zero.
            missing.append(name)
            continue
        counted.append(name)
        for field, value in valid.items():
            tokens[field] += value
        if round_cost is not None:
            cost = round_cost if cost is None else cost + round_cost
        round_models = usage.get("models")
        if isinstance(round_models, dict):
            models.update(str(m) for m in round_models)

    if not counted:
        reason = "no round recorded runtime usage"
        if invalid:
            reason += f"; malformed figures in {', '.join(invalid)}"
        return {"available": False, "reason": reason}
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
    if invalid:
        result["rounds_with_malformed_usage"] = invalid
    return result


# --- subagent-transcript source --------------------------------------------------


def _read_records(path: Path) -> list[dict[str, Any]] | None:
    """Parsed records of a .jsonl transcript, or None when the file cannot be read.

    An unparseable line is skipped (a transcript being written can end mid-line);
    an unreadable file is reported by the caller, not counted as an empty one.
    """
    records: list[dict[str, Any]] = []
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
                    records.append(record)
    except (OSError, UnicodeDecodeError):
        return None
    return records


def summarize_agent(transcript: Path) -> dict[str, Any]:
    """Total one subagent transcript's usage, once per API response.

    Claude Code writes one record per content block of a response, each repeating
    that response's `usage`, so records sharing `(requestId, message.id)` are one
    response: the record with the largest `output_tokens` stands for it (a
    streamed response's last record carries the final count). A record with
    neither id is counted on its own.
    """
    records = _read_records(transcript)
    tokens = _empty_tokens()
    models: set[str] = set()
    responses: dict[object, dict[str, Any]] = {}
    for index, record in enumerate(records or []):
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        model = message.get("model")
        if isinstance(model, str):
            models.add(model)
        request_id, message_id = record.get("requestId"), message.get("id")
        key: object = (
            (str(request_id), str(message_id))
            if isinstance(request_id, str) or isinstance(message_id, str)
            else index
        )
        kept = responses.get(key)
        if kept is None or (_int(usage.get("output_tokens")) or 0) > (
            _int(kept.get("output_tokens")) or 0
        ):
            responses[key] = usage
    for usage in responses.values():
        for field in TOKEN_FIELDS:
            tokens[field] += _int(usage.get(field)) or 0
    messages = len(responses)
    meta = _read_json(transcript.with_name(f"{transcript.stem}.meta.json"))
    description = meta.get("description") if isinstance(meta, dict) else None
    return {
        "agent_id": transcript.stem,
        "readable": records is not None,
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
    missing = [sid for sid in session_ids if sid not in located]
    unreadable = [a["agent_id"] for a in agents if not a["readable"]]
    gaps = []
    if missing:
        gaps.append(f"no transcript directory for session(s) {', '.join(missing)}")
    if unreadable:
        gaps.append(f"unreadable transcript(s) {', '.join(unreadable)}")
    result: dict[str, Any] = {
        # A located session with no subagents/ directory is a real zero: the
        # transcript exists and the lane dispatched nothing.
        "available": True,
        # False when a session or transcript the lane had could not be read: the
        # totals are then a lower bound, and the flat `subagent_tokens` is None.
        "complete": not gaps,
        "agent_count": len(agents),
        "tokens": tokens,
        "total_tokens": sum(tokens.values()),
        "agents": sorted(agents, key=lambda a: -sum(a["tokens"].values())),
    }
    if gaps:
        result["reason"] = "; ".join(gaps)
    return result


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
    docstring gives. Each is None when its source is unavailable, never 0, and
    `subagent_tokens` is also None when the transcript sum is incomplete.
    """
    result, subagents = row["result"], row["subagents"]
    row["tokens"] = result.get("total_tokens") if result.get("available") else None
    row["cost_usd"] = result.get("total_cost_usd") if result.get("available") else None
    row["subagent_tokens"] = (
        subagents.get("total_tokens")
        if subagents.get("available") and subagents.get("complete")
        else None
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


def _has_usage(row: dict[str, Any]) -> bool:
    """A lane has usage when either source gave a complete figure.

    A transcript sum with an unreadable transcript or a missing session is a lower
    bound, not a measurement, so it does not count here (nor for `--strict`).
    """
    return row["tokens"] is not None or row["subagent_tokens"] is not None


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
            if not _has_usage(r)
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
    primary: Path | None = None
    if first.startswith(b"worktree "):
        primary = Path(os.fsdecode(first[len(b"worktree "):]))
    # As repo_root.sh: a separate git dir or a submodule lists its git directory,
    # not a checkout, first; fall back to the invoking checkout's root then.
    if primary is None or not primary.is_absolute() or not (primary / ".git").exists():
        try:
            top = subprocess.run(
                ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                capture_output=True,
                check=True,
                timeout=30,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
        if not top:
            return None
        primary = Path(os.fsdecode(top))
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
    if report["lanes_without_usage"]:
        lines.append("")
        lines.append(
            "no usage recorded from either source: "
            + ", ".join(report["lanes_without_usage"])
        )
    notes = []
    for row in report["lanes"]:
        for source in ("result", "subagents"):
            reason = row[source].get("reason")
            if reason:
                notes.append(f"  {row['scope']} {source}: {reason}")
    if notes:
        lines.append("")
        lines.append("gaps:")
        lines.extend(notes)
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

    if not sessions_dir.is_dir():
        print(f"error: sessions directory not found: {sessions_dir}", file=sys.stderr)
        return 2

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
    any_usage = any(_has_usage(r) for r in report["lanes"])
    return 1 if args.strict and not any_usage else 0


if __name__ == "__main__":
    sys.exit(main())
