"""Build or verify the review-finding digest from the run's raw bundle."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from triage.canonical import CanonicalError, dumps

from . import artifacts, identity, normalize
from .config import Settings
from .errors import SystemizeError
from .fetch import all_targets


def load_raw(settings: Settings, *, mode: str, window_days: int, date: str) -> tuple[Path, dict[str, Any]]:
    """Read the raw bundle and require every identity field derivable locally.

    ``forge_repo`` and ``protected_branch_head`` cannot be re-derived without a
    second forge read, during which the head may legitimately move, so they are
    taken from the validated bundle; everything else must match this invocation.
    """
    logical = artifacts.render(settings.cache_pattern, date=date, window_days=window_days, mode=mode)
    path = artifacts.state_read_path(settings, logical)
    raw = identity.parse_artifact(artifacts.read_regular(path, "cache"), str(path))
    run_id = identity.check_header(raw, kind=identity.RAW_KIND, path=str(path))
    expected = {
        "schema": identity.RUN_SCHEMA,
        "window_days": window_days,
        "config_fingerprint": settings.fingerprint,
        "execution_mode": mode,
    }
    for key, value in expected.items():
        if run_id.get(key) != value:
            raise SystemizeError(
                f"{path}: raw bundle {key} {run_id.get(key)!r} does not match this run ({value!r}); "
                "refetch for this window, mode and configuration"
            )
    if set(run_id) != {*expected, "forge_repo", "protected_branch_head"}:
        raise SystemizeError(f"{path}: raw bundle run_identity has unexpected fields")
    if not isinstance(run_id.get("forge_repo"), str) or not re.fullmatch(
        r"[0-9a-f]{40}", str(run_id.get("protected_branch_head"))
    ):
        raise SystemizeError(f"{path}: raw bundle lacks a forge repository or protected-branch head")
    if not isinstance(raw.get("prs"), list):
        raise SystemizeError(f"{path}: raw bundle has no prs[] population")
    return path, raw


def run(settings: Settings, *, mode: str, window_days: int, date: str, verify_path: Path | None) -> dict[str, Any]:
    window_days = settings.window_days_for(window_days)
    raw_path, raw = load_raw(settings, mode=mode, window_days=window_days, date=date)
    expected = normalize.build(raw, settings, normalize.instruction_paths(settings.root))

    if verify_path is not None:
        candidate = identity.parse_artifact(artifacts.read_regular(verify_path, "digest"), str(verify_path))
        normalize.verify(candidate, expected, str(verify_path))
        return {
            "engine": "digest",
            "verified": str(verify_path),
            "cache_path": str(raw_path),
            "run_identity_digest": expected["run_identity_digest"],
        }

    targets = all_targets(settings, date=date, window_days=window_days, mode=mode)
    artifacts.check_targets(settings, targets)
    digest_target = next(t for t in targets if t.label == "digest")
    artifacts.require_replaceable(digest_target, kind=identity.DIGEST_KIND, identity=raw["run_identity"])
    try:
        data = dumps(expected)
    except CanonicalError as exc:
        raise SystemizeError(f"digest is not canonical JSON: {exc}") from exc
    artifacts.check_targets(settings, targets)
    artifacts.publish(digest_target, data)
    return {
        "engine": "digest",
        "cache_path": str(raw_path),
        "digest_path": str(digest_target.path),
        "run_identity_digest": expected["run_identity_digest"],
        "findings_pr_count": expected["findings_pr_count"],
        "single_pass_recommended": expected["single_pass_recommended"],
        "n_batches": expected["n_batches"],
        "input_cap_applied": expected["input_cap"]["applied"],
    }
