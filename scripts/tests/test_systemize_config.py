"""Merged-config validation and fingerprinting for the systemize engines."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir  # noqa: E402

sys.path.insert(0, str(engine_dir(Path(__file__)) / "lib"))
from systemize.config import (  # noqa: E402
    REQUIRED_KEYS,
    fingerprint,
    load_settings,
    normalize_login,
)
from systemize.errors import SystemizeError  # noqa: E402
from test_systemize_support import ENGINES, engines_rel, make_repo  # noqa: E402


def _set(key: str, value: str):
    def edit(text: str) -> str:
        pattern = re.compile(rf"^(  {key}:).*$", re.MULTILINE)
        assert pattern.search(text[text.index("\nsystemize:"):]), key
        head, tail = text.split("\nsystemize:", 1)
        return head + "\nsystemize:" + pattern.sub(lambda m: f"{m.group(1)} {value}", tail, count=1)
    return edit


def _drop(key: str):
    def edit(text: str) -> str:
        head, tail = text.split("\nsystemize:", 1)
        return head + "\nsystemize:" + re.sub(rf"^  {key}:.*\n", "", tail, count=1, flags=re.MULTILINE)
    return edit


def test_shipped_config_loads_engine_backed(tmp_path: Path) -> None:
    settings = load_settings(make_repo(tmp_path))
    assert settings.engine_mode == "engine-backed"
    assert settings.heartbeat_job == "post-merge-systemize"
    assert "coderabbitai[bot]" in settings.reviewer_logins


@pytest.mark.parametrize("key", REQUIRED_KEYS)
def test_a_missing_required_key_is_named(tmp_path: Path, key: str) -> None:
    with pytest.raises(SystemizeError, match=rf"missing config key systemize\.{key}: rerun ./init.sh"):
        load_settings(make_repo(tmp_path, config_edit=_drop(key)))


@pytest.mark.parametrize("key", ("heartbeat_job", "heartbeat_pattern"))
def test_heartbeat_keys_are_required_only_engine_backed(tmp_path: Path, key: str) -> None:
    with pytest.raises(SystemizeError, match=rf"systemize\.{key}"):
        load_settings(make_repo(tmp_path, config_edit=_drop(key)))
    llm_only = make_repo(tmp_path / "llm", engines=(), config_edit=_drop(key))
    assert load_settings(llm_only).engine_mode == "llm-only"


@pytest.mark.parametrize(
    "key, value, message",
    [
        ("lookback_days", "true", "positive integer"),
        ("lookback_days", "0", "positive integer"),
        ("batch_size", "-1", "positive integer"),
        ("batch_size", '"25"', "positive integer"),
        ("pattern_threshold", "1", "at least 2"),
        ("backfill_days", "3", "at least systemize.lookback_days"),
        ("batch_size", "61", "batch_size <= single_pass_max_prs"),
        ("single_pass_max_prs", "76", "batch_size <= single_pass_max_prs"),
        ("pattern_threshold", "76", "must not exceed"),
        ("tracker_severity", "major", "tracker_severity must be one of"),
        ("operator_logins", "[Topi, ' topi ']", "unique after normalization"),
        ("operator_logins", '[""]', "non-empty"),
        ("analysis_tier", "turbo", "analysis_tier"),
        ("pr_draft", "true", "pr_draft must be false"),
        ("commit_subject", '""', "commit_subject"),
        ("cache_pattern", '"state/cache/merged-prs_{window}_{mode}.json"', "must contain {date}"),
        ("cache_pattern", '"/tmp/x_{date}_{window}_{mode}.json"', "repository-relative"),
        ("digest_cache_pattern", '"state/../x_{date}_{window}_{mode}.json"', "repository-relative"),
        ("digest_cache_pattern", '"cache/x_{date}_{window}_{mode}.json"', "begin with state.dirname"),
        ("report_root", ".", "must not be the repository root"),
        ("report_pattern", '"elsewhere/r_{date}_{window}_{mode}.md"', "beneath systemize.report_root"),
        ("heartbeat_pattern", '"state/cache/merged-prs_{window}_{mode}_{date}.json"', "collide"),
        ("heartbeat_job", '""', "heartbeat_job"),
        ("fetch_engine", "../fetch.py", "filename beneath paths.engines"),
    ],
)
def test_invalid_values_stop_naming_the_invariant(tmp_path: Path, key, value, message) -> None:
    with pytest.raises(SystemizeError, match=re.escape(message)):
        load_settings(make_repo(tmp_path, config_edit=_set(key, value)))


def test_an_empty_trusted_source_union_stops(tmp_path: Path) -> None:
    def edit(text: str) -> str:
        return text.replace("  bots: [coderabbit]\n", "  bots: []\n", 1)
    with pytest.raises(SystemizeError, match="no trusted review source"):
        load_settings(make_repo(tmp_path, config_edit=edit))


def test_aliases_are_trusted_only_when_listed(tmp_path: Path) -> None:
    settings = load_settings(make_repo(tmp_path))
    assert settings.reviewer_logins == {"coderabbit", "coderabbitai", "coderabbitai[bot]"}
    assert "coderabbit-shim" not in settings.reviewer_logins


def test_login_normalization_lowercases_ascii_only() -> None:
    assert normalize_login("  TöPi\t") == "töpi"
    assert normalize_login("ÄB") == "Äb"


def test_the_state_resolver_is_required(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / engines_rel(root) / "lib/state_paths/__init__.py").unlink()
    with pytest.raises(SystemizeError, match="state-path resolver missing"):
        load_settings(root)


def test_state_dirname_must_match_the_resolver(tmp_path: Path) -> None:
    def edit(text: str) -> str:
        return re.sub(r"^(\s+dirname:).*$", r"\1 var", text, count=1, flags=re.MULTILINE)
    with pytest.raises(SystemizeError, match="STATE_DIRNAME"):
        load_settings(make_repo(tmp_path, config_edit=edit))


@pytest.mark.parametrize("missing", ENGINES)
def test_a_partial_engine_set_stops(tmp_path: Path, missing: str) -> None:
    root = make_repo(tmp_path, engines=tuple(e for e in ENGINES if e != missing))
    with pytest.raises(SystemizeError, match="partial"):
        load_settings(root)


def test_the_fingerprint_is_sha256_of_the_canonical_wrapper() -> None:
    config = {"b": [1, True, None], "a": {"é": "x"}}
    canonical = '{"config":{"a":{"é":"x"},"b":[1,true,null]},"schema":"post-merge-systemize-config-v1"}'
    assert fingerprint(config) == "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


@pytest.mark.parametrize("bad", [{1: "x"}, {"x": float("inf")}, {"x": object()}])
def test_the_fingerprint_rejects_non_canonical_values(bad) -> None:
    with pytest.raises(SystemizeError, match="cannot be fingerprinted"):
        fingerprint(bad)


def test_the_overlay_is_part_of_the_fingerprint(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    before = load_settings(root).fingerprint
    (root / "config/dev-model.local.yaml").write_text('notify:\n  user_key: "U1"\n', encoding="utf-8")
    after = load_settings(root)
    assert after.config["notify"]["user_key"] == "U1"
    assert after.fingerprint != before
    assert json.dumps(after.config)  # still a JSON-able merged view
