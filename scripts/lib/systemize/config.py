"""Merged-config validation and the resumability fingerprint.

Every check here restates a sentence of the shared workflow's *Resolve
configuration* section; the workflow is the contract and this is its executable
reading. A failed check raises :class:`SystemizeError` naming the invariant, and
nothing is coerced or repaired in memory — the operator corrects the shared
configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from kitconfig import load_config, repo_root
from triage.canonical import CanonicalError, digest

from .errors import SystemizeError

CANONICAL_SEVERITIES = ("low", "normal", "high", "critical")
CONFIG_SCHEMA = "post-merge-systemize-config-v1"
ARTIFACT_PLACEHOLDERS = ("{date}", "{window}", "{mode}")

REQUIRED_KEYS = (
    "analysis_tier",
    "lookback_days",
    "operator_logins",
    "backfill_days",
    "pattern_threshold",
    "tracker_severity",
    "batch_size",
    "single_pass_max_prs",
    "max_findings_prs_per_run",
    "cache_pattern",
    "digest_cache_pattern",
    "report_root",
    "report_pattern",
    "fetch_engine",
    "digest_engine",
    "heartbeat_engine",
    "commit_subject",
    "pr_draft",
)
# Required only when the complete engine set is installed: an LLM-only run has
# no heartbeat, so an adopter config predating these keys keeps working there.
HEARTBEAT_KEYS = ("heartbeat_job", "heartbeat_pattern")
POSITIVE_INT_KEYS = (
    "lookback_days",
    "backfill_days",
    "pattern_threshold",
    "batch_size",
    "single_pass_max_prs",
    "max_findings_prs_per_run",
)
# Repository control inputs no artifact may land on, tracked or not.
CONTROL_INPUTS = (
    "AGENTS.md",
    "CLAUDE.md",
    "docs/agentic-dev-kit/workflows/post-merge-systemize.md",
)


@dataclass(frozen=True)
class Settings:
    root: Path
    config: dict[str, Any]
    fingerprint: str
    engine_dir: Path
    engine_mode: str  # "engine-backed" or "llm-only"
    protected_branch: str
    state_dirname: str
    lookback_days: int
    backfill_days: int
    pattern_threshold: int
    tracker_severity: str
    batch_size: int
    single_pass_max_prs: int
    max_findings_prs_per_run: int
    operator_logins: tuple[str, ...]
    reviewer_logins: frozenset[str]
    cache_pattern: str
    digest_pattern: str
    report_root: str
    report_pattern: str
    heartbeat_job: str | None
    heartbeat_pattern: str | None
    control_inputs: tuple[Path, ...]

    def window_days_for(self, requested: int) -> int:
        if requested not in (self.lookback_days, self.backfill_days):
            raise SystemizeError(
                f"--window-days {requested} is neither systemize.lookback_days "
                f"({self.lookback_days}) nor systemize.backfill_days ({self.backfill_days})"
            )
        return requested


def normalize_login(value: str) -> str:
    """Trim ASCII whitespace and lowercase ASCII letters only (workflow rule)."""
    trimmed = value.strip(" \t\n\r\x0b\x0c")
    return "".join(ch.lower() if "A" <= ch <= "Z" else ch for ch in trimmed)


def fingerprint(config: dict[str, Any]) -> str:
    try:
        return "sha256:" + digest({"schema": CONFIG_SCHEMA, "config": config})
    except CanonicalError as exc:
        raise SystemizeError(f"config cannot be fingerprinted: {exc}") from exc


def _get(config: dict[str, Any], dotted: str) -> Any:
    node: Any = config
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise SystemizeError(
                f"missing config key {dotted}: rerun ./init.sh or add the documented value"
            )
        node = node[part]
    return node


def _positive_int(section: dict[str, Any], key: str) -> int:
    value = section[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SystemizeError(f"systemize.{key} must be a positive integer, got {value!r}")
    return value


def _nonempty_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemizeError(f"{name} must be a non-empty string")
    return value


def _relative_fragment(value: Any, name: str) -> str:
    text = _nonempty_str(value, name)
    pure = PurePosixPath(text)
    if pure.is_absolute() or text.startswith("~") or ".." in pure.parts:
        raise SystemizeError(f"{name} must be a repository-relative path without '..'")
    return text


def _artifact_pattern(value: Any, name: str) -> str:
    text = _relative_fragment(value, name)
    missing = [p for p in ARTIFACT_PLACEHOLDERS if p not in text]
    if missing:
        raise SystemizeError(f"{name} must contain {', '.join(missing)}")
    return text


def _logins(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise SystemizeError(f"{name} must be a sequence of forge logins")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not normalize_login(item):
            raise SystemizeError(f"{name} entries must be non-empty strings")
        normalized.append(normalize_login(item))
    if len(normalized) != len(set(normalized)):
        raise SystemizeError(f"{name} entries must be unique after normalization")
    return tuple(normalized)


def _reviewer_logins(config: dict[str, Any]) -> frozenset[str]:
    review = config.get("review") or {}
    bots = review.get("bots") or []
    aliases = review.get("bot_author_aliases") or {}
    if not isinstance(bots, list) or not isinstance(aliases, dict):
        raise SystemizeError("review.bots must be a sequence and review.bot_author_aliases a mapping")
    trusted: set[str] = set()
    for bot in bots:
        if not isinstance(bot, str) or not normalize_login(bot):
            raise SystemizeError("review.bots entries must be non-empty strings")
        trusted.add(normalize_login(bot))
        listed = aliases.get(bot, [])
        if not isinstance(listed, list):
            raise SystemizeError(f"review.bot_author_aliases.{bot} must be a sequence")
        for alias in listed:
            if not isinstance(alias, str) or not normalize_login(alias):
                raise SystemizeError(f"review.bot_author_aliases.{bot} entries must be non-empty strings")
            trusted.add(normalize_login(alias))
    return frozenset(trusted)


def _engine_mode(engine_dir: Path, section: dict[str, Any]) -> str:
    present = []
    for key in ("fetch_engine", "digest_engine", "heartbeat_engine"):
        name = _nonempty_str(section[key], f"systemize.{key}")
        if PurePosixPath(name).name != name:
            raise SystemizeError(f"systemize.{key} must be a filename beneath paths.engines")
        present.append((engine_dir / name).is_file())
    if all(present):
        return "engine-backed"
    if not any(present):
        return "llm-only"
    raise SystemizeError(
        "configured fetch/digest/heartbeat engine set is partial: install all three "
        "under paths.engines or remove all three"
    )


def load_settings(start: Path | None = None) -> Settings:
    root = repo_root(start).resolve()
    try:
        config = load_config(root / "config/dev-model.yaml")
    except (OSError, ValueError) as exc:
        raise SystemizeError(f"merged config unreadable: {exc}") from exc
    section = _get(config, "systemize")
    if not isinstance(section, dict):
        raise SystemizeError("systemize must be a mapping")
    for key in REQUIRED_KEYS:
        _get(config, f"systemize.{key}")

    ints = {key: _positive_int(section, key) for key in POSITIVE_INT_KEYS}
    if ints["pattern_threshold"] < 2:
        raise SystemizeError("systemize.pattern_threshold must be at least 2")
    if ints["backfill_days"] < ints["lookback_days"]:
        raise SystemizeError("systemize.backfill_days must be at least systemize.lookback_days")
    if not ints["batch_size"] <= ints["single_pass_max_prs"] <= ints["max_findings_prs_per_run"]:
        raise SystemizeError(
            "systemize.batch_size <= single_pass_max_prs <= max_findings_prs_per_run must hold"
        )
    if ints["pattern_threshold"] > ints["max_findings_prs_per_run"]:
        raise SystemizeError("systemize.pattern_threshold must not exceed max_findings_prs_per_run")

    severity = section["tracker_severity"]
    if severity not in CANONICAL_SEVERITIES:
        raise SystemizeError(f"systemize.tracker_severity must be one of {', '.join(CANONICAL_SEVERITIES)}")
    operators = _logins(section["operator_logins"], "systemize.operator_logins")
    reviewers = _reviewer_logins(config)
    if not operators and not reviewers:
        raise SystemizeError(
            "no trusted review source: configure systemize.operator_logins or review.bots"
        )

    tiers = _get(config, "models.tiers")
    if not isinstance(tiers, dict) or section["analysis_tier"] not in tiers:
        raise SystemizeError("systemize.analysis_tier must name a key under models.tiers")
    _nonempty_str(section["commit_subject"], "systemize.commit_subject")
    if section["pr_draft"] is not False:
        raise SystemizeError("systemize.pr_draft must be false")
    protected = _nonempty_str(_get(config, "vcs.protected_branch"), "vcs.protected_branch")

    engines_rel = _relative_fragment(_get(config, "paths.engines"), "paths.engines")
    engine_dir = (root / engines_rel).resolve()
    if not engine_dir.is_relative_to(root):
        raise SystemizeError("paths.engines escapes the repository")
    resolver_dir = engine_dir / "lib" / "state_paths"
    if not (resolver_dir / "__init__.py").is_file():
        raise SystemizeError(f"shared state-path resolver missing at {resolver_dir}")
    from state_paths.resolver import STATE_DIRNAME

    state_dirname = _get(config, "state.dirname")
    if state_dirname != STATE_DIRNAME:
        raise SystemizeError(
            f"state.dirname {state_dirname!r} does not match the resolver's STATE_DIRNAME {STATE_DIRNAME!r}"
        )

    cache = _artifact_pattern(section["cache_pattern"], "systemize.cache_pattern")
    digest_pattern = _artifact_pattern(section["digest_cache_pattern"], "systemize.digest_cache_pattern")
    report_root_rel = _relative_fragment(section["report_root"], "systemize.report_root")
    if PurePosixPath(report_root_rel) in (PurePosixPath("."), PurePosixPath("")):
        raise SystemizeError("systemize.report_root must not be the repository root")
    report = _artifact_pattern(section["report_pattern"], "systemize.report_pattern")
    if not PurePosixPath(report).is_relative_to(PurePosixPath(report_root_rel)):
        raise SystemizeError("systemize.report_pattern must resolve beneath systemize.report_root")
    for name, value in (("cache_pattern", cache), ("digest_cache_pattern", digest_pattern)):
        if not value.startswith(STATE_DIRNAME + "/"):
            raise SystemizeError(f"systemize.{name} must begin with state.dirname/")

    mode = _engine_mode(engine_dir, section)
    job: str | None = None
    heartbeat: str | None = None
    if mode == "engine-backed":
        for key in HEARTBEAT_KEYS:
            _get(config, f"systemize.{key}")
        job = _nonempty_str(section["heartbeat_job"], "systemize.heartbeat_job")
        heartbeat = _artifact_pattern(section["heartbeat_pattern"], "systemize.heartbeat_pattern")
        if not heartbeat.startswith(STATE_DIRNAME + "/"):
            raise SystemizeError("systemize.heartbeat_pattern must begin with state.dirname/")

    rendered = [p for p in (cache, digest_pattern, report, heartbeat) if p is not None]
    if len(rendered) != len(set(rendered)):
        raise SystemizeError("configured systemize artifact patterns collide")

    controls = [root / "config/dev-model.yaml", root / "config/dev-model.local.yaml"]
    controls += [root / rel for rel in CONTROL_INPUTS]
    for key in ("paths.friction_log", "paths.handoff"):
        value = _get(config, key)
        if isinstance(value, str) and value:
            controls.append(root / value)
    controls += [engine_dir / section[k] for k in ("fetch_engine", "digest_engine", "heartbeat_engine")]

    return Settings(
        root=root,
        config=config,
        fingerprint=fingerprint(config),
        engine_dir=engine_dir,
        engine_mode=mode,
        protected_branch=protected,
        state_dirname=STATE_DIRNAME,
        lookback_days=ints["lookback_days"],
        backfill_days=ints["backfill_days"],
        pattern_threshold=ints["pattern_threshold"],
        tracker_severity=severity,
        batch_size=ints["batch_size"],
        single_pass_max_prs=ints["single_pass_max_prs"],
        max_findings_prs_per_run=ints["max_findings_prs_per_run"],
        operator_logins=operators,
        reviewer_logins=reviewers,
        cache_pattern=cache,
        digest_pattern=digest_pattern,
        report_root=report_root_rel,
        report_pattern=report,
        heartbeat_job=job,
        heartbeat_pattern=heartbeat,
        control_inputs=tuple(Path(os.path.abspath(p)) for p in controls),
    )
