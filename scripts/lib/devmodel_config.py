"""Tiny loader for ``config/dev-model.yaml`` — the kit's single config surface.

Every kit script reads project-specific values (paths, tracker ids, doc
budgets, ...) through this module instead of hardcoding them (the kit's
"No hardcoding" principle). Stdlib + PyYAML only, on purpose: no other
dependency should ever be required just to read a config value.

Usage:
    from devmodel_config import get, load_config, resolve_path

    config = load_config()                    # config/dev-model.yaml
    budgets = get(config, "doc_budgets")       # fail-loud if absent
    forge = get(config, "vcs.forge", "github")  # optional, with a default
    handoff = resolve_path(config, "paths.handoff")  # -> absolute Path
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = "config/dev-model.yaml"

# Sentinel so `get()` can tell "no default supplied" apart from a legitimate
# default value of None.
_MISSING = object()


def _repo_root() -> Path:
    """Walk up from this file to the nearest ``.git`` ancestor.

    The kit's repo-root discovery uses `.git` only — a copy-in kit always
    runs from inside the target repo.
    """
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    # No .git found (e.g. the kit was copied in but `git init` hasn't run
    # yet) — fall back to two levels up from scripts/lib/.
    return here.parents[2]


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and parse ``config/dev-model.yaml``.

    Raises ``FileNotFoundError`` if the file is missing — a script that needs
    config has nothing sane to fall back to.
    """
    p = Path(path)
    if not p.is_absolute():
        p = _repo_root() / p
    if not p.is_file():
        raise FileNotFoundError(f"dev-model config not found: {p} (run ./init.sh, or pass an explicit path)")
    with p.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def get(config: dict[str, Any], dotted_key: str, default: Any = _MISSING) -> Any:
    """Look up a dotted key (e.g. ``"paths.handoff"``) in a loaded config dict.

    Fail-loud (``KeyError``) when the key is missing and no ``default`` is
    given — a required config key silently reading as ``None`` would let a
    script write to the wrong path with no signal. Pass ``default=`` for a
    genuinely optional key.
    """
    node: Any = config
    parts = dotted_key.split(".")
    for i, part in enumerate(parts):
        if not isinstance(node, dict) or part not in node:
            if default is not _MISSING:
                return default
            raise KeyError(f"required config key '{dotted_key}' not found (missing at '{'.'.join(parts[: i + 1])}')")
        node = node[part]
    return node


def resolve_path(config: dict[str, Any], dotted_key: str, *, root: Path | None = None) -> Path:
    """Resolve a config path value (e.g. ``"paths.handoff"``) to an absolute ``Path``.

    A relative value in the config resolves against the repo root (or
    ``root`` if given); an already-absolute value passes through unchanged.
    """
    value = get(config, dotted_key)
    p = Path(str(value))
    if p.is_absolute():
        return p
    return (root or _repo_root()) / p
