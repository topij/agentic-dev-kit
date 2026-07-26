"""Stdlib-only reader for ``config/dev-model.yaml`` — the kit's single config surface.

Why not PyYAML: the kit's engines are deliberately dependency-free where they sit
in a hot loop (``pr_watch.py`` declares ``dependencies = []``) or run from a git
hook, so *requiring* a third-party parser just to read a config value is what
forces adopters to hardcode the value into the engine instead — the exact
Principle #10 failure the config surface exists to prevent.

This parses the **deliberately simple, hand-authored** subset the kit's config
actually uses, and nothing else:

- nested block mappings (``review:`` / ``linear:`` / ``tiers:``), any depth
- scalars, with ``#`` comments stripped and one layer of matching quotes removed
- inline flow lists — ``bots: [coderabbit, bugbot]`` / ``[]``
- block lists of scalars (``- coderabbit``)
- block lists of mappings (``doc_budgets``)
- ``true``/``false``/``null`` and integers coerced to Python types

It is **not** a YAML implementation: no anchors, no multi-line scalars, no flow
mappings, no multi-document streams. A construct it does not understand is
skipped rather than guessed at. If you need those, keep using
``devmodel_config.py`` (PyYAML-backed) — the two agree on every construct this
one supports, which the test suite pins.

Usage:
    from kitconfig import get, load_config

    config = load_config()                              # config/dev-model.yaml
    branch = get(config, "vcs.protected_branch")         # fail-loud if absent
    bots = get(config, "review.bots", [])                # optional, with default
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = "config/dev-model.yaml"

# A dash item opens a MAPPING only when it really looks like `key: value` —
# YAML requires the colon be followed by whitespace or end-of-line. Testing for
# a bare `":" in body` instead turns `- https://example.com` into
# {"https": "//example.com"}: a silent guess, which this module's contract
# explicitly forbids in favour of skipping.
_DASH_MAPPING_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*:(?:\s|$)")

# Sentinel so `get()` can distinguish "no default supplied" from a legitimate
# default of None.
_MISSING = object()

# How far above the engine file `repo_root`'s config-marker fallback may look.
# 4 == `here.parents[:4]`, i.e. the file plus four directories up, which reaches
# the root of both prescribed layouts (`scripts/lib/`, `scripts/devkit/lib/`).
# It exists to stop the walk escaping into a parent project — see repo_root.
_CONFIG_PROBE_MAX_PARENTS = 4


def repo_root(start: Path | None = None) -> Path:
    """Nearest ancestor carrying a ``.git`` entry (dir in a checkout, file in a
    linked worktree). Walking up for the marker — rather than counting
    ``parents[N]`` — is what lets the kit be vendored at any depth
    (``scripts/devkit/lib/``) without rewriting a single path.

    Both probes walk. The config probe is the fallback for a tree with no
    ``.git`` at all — an exported tarball, a ``GIT_DIR``-only setup — where the
    old ``parents[2]`` arithmetic silently returned the wrong directory for any
    layout other than the kit's own ``scripts/lib/``. From ``scripts/devkit/lib/``
    (the layout this docstring names, and the one ``/adopt`` prescribes when the
    adopter's ``scripts/`` has colliding names) it yielded ``<repo>/scripts``,
    and ``load_config`` then reported a missing config at a path that never
    existed. See issue #60.

    The config probe is BOUNDED; the ``.git`` probe is not. Unbounded, the
    config walk reaches ``/`` and selects a FOREIGN ``config/dev-model.yaml``
    sitting above a ``.git``-less tree, returning a different project's root —
    which ``archive_plan_sessions`` would then rewrite. That was measurably
    WORSE than the arithmetic it replaced, which resolves the kit's own layout
    correctly in exactly that case. A wrong LOUD answer (``FileNotFoundError``
    naming a path that does not exist) beats a wrong SILENT one.

    ``_CONFIG_PROBE_MAX_PARENTS`` covers every layout the kit prescribes:

    ==========================================  =================
    layout                                      root
    ==========================================  =================
    ``<root>/scripts/lib/`` (the kit's own)     ``parents[2]``
    ``<root>/scripts/devkit/lib/`` (/adopt's)   ``parents[3]``
    ==========================================  =================

    Vendoring deeper than that still resolves through ``.git``, which every real
    checkout has and which is unbounded — the bound constrains only the
    no-``.git`` fallback.

    ``parents[2]`` survives as the last resort when neither marker is found —
    nothing better is knowable at that point.
    """
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    for candidate in (here, *here.parents[:_CONFIG_PROBE_MAX_PARENTS]):
        if (candidate / DEFAULT_CONFIG_PATH).is_file():
            return candidate
    return here.parents[2] if len(here.parents) >= 3 else here.parent


def _strip_comment(value: str) -> str:
    """Drop a trailing ``#`` comment that is outside quotes.

    Naive splitting on ``#`` would truncate a legitimate value containing one
    (a URL fragment, a branch pattern). Track quote state instead.
    """
    quote: str | None = None
    for i, ch in enumerate(value):
        if quote is None and ch in ("'", '"'):
            quote = ch
        elif quote is not None and ch == quote:
            quote = None
        # Only a `#` preceded by whitespace (or at the start) opens a comment,
        # matching YAML — so `chore/triage-{date}#1` keeps its suffix.
        elif quote is None and ch == "#" and (i == 0 or value[i - 1] in (" ", "\t")):
            return value[:i]
    return value


# Transcribed from PyYAML's own float resolver, not approximated from it — the
# sign rules are asymmetric in a way no reasonable guess reproduces:
#   - the exponent's [-+] is REQUIRED  (`1.0e+3` is a float, `1.0e3` a string)
#   - a leading sign is allowed on `digits.digits` but NOT on `.digits`
#     (`-0.5` is a float, `-.5` a string)
#   - `_` is a digit separator anywhere in the mantissa (`1_0.5` -> 10.5)
# Omits PyYAML's `.inf` / `.nan` / sexagesimal (`1:30.0`) branches — see _coerce.
_YAML_FLOAT_RE = re.compile(
    r"""^(?:
          [-+]? [0-9][0-9_]* \. [0-9_]*  (?:[eE][-+][0-9]+)?   # 1.  1.5  -0.5  1_0.5
        |        \.          [0-9][0-9_]* (?:[eE][-+][0-9]+)?  # .5   (unsigned only)
        )$""",
    re.VERBOSE,
)


def _coerce(raw: str) -> Any:
    """Turn one scalar token into a Python value."""
    text = _strip_comment(raw).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    if text in ("", "~", "null"):
        return None
    low = text.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(text)
    except ValueError:
        pass
    # Floats, matched against YAML 1.1's own resolver rather than handed to
    # `float()`. `float()` accepts `nan`, `inf` and `1e5`, and PyYAML resolves
    # all three as STRINGS — so the loose version would trade one divergence
    # from the parity invariant for three more. Note the exponent's sign is
    # mandatory: PyYAML reads `1.0e+3` as 1000.0 but `1.0e3` as the string
    # "1.0e3", and matching that exactly is the whole point of using its rule
    # instead of an approximation of it.
    #
    # Two known, deliberate gaps remain, both pinned by the parity test: YAML
    # 1.1's `.inf` / `.nan` special forms, and its sexagesimal floats (`1:30.0`
    # → 90.0). Neither is meaningful as a config value in this kit, and
    # supporting them would mean carrying YAML's special-form table for no
    # adopter benefit.
    if _YAML_FLOAT_RE.match(text):
        try:
            return float(text.replace("_", ""))  # `_` is a YAML digit separator
        except ValueError:  # pragma: no cover — the pattern already guarantees this
            return text
    return text


def _parse_flow_list(text: str) -> list[Any]:
    """``[a, b, "c d"]`` -> ``["a", "b", "c d"]``. Empty ``[]`` -> ``[]``."""
    inner = text.strip()[1:-1].strip()
    if not inner:
        return []
    items: list[str] = []
    current = ""
    quote: str | None = None
    for ch in inner:
        if quote is None and ch in ("'", '"'):
            quote = ch
            current += ch
        elif quote is not None and ch == quote:
            quote = None
            current += ch
        elif quote is None and ch == ",":
            items.append(current)
            current = ""
        else:
            current += ch
    items.append(current)
    return [_coerce(item) for item in items if item.strip()]


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def loads(text: str) -> dict[str, Any]:
    """Parse the supported subset of a config document into nested dicts/lists."""
    # Each frame is (indent, container, kind). Dedenting pops frames until the
    # indent matches — but a LIST frame pops on a different rule than a mapping
    # frame, because YAML lets a block list sit at the SAME indent as its key:
    #
    #     doc_budgets:          doc_budgets:
    #     - path: a       vs      - path: a
    #       budget: 1               budget: 1
    #
    # Both are valid and both appear in the wild (formatters emit the left one).
    # A single `indent <= frame_indent` rule handles only the right one and
    # silently corrupts the left — the list is never created, its dashes are
    # dropped, and its nested keys land in the PARENT mapping.
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any, str]] = [(-1, root, "map")]

    def pop_to(indent: int, *, for_dash: bool) -> None:
        # A mapping frame closes when a line is at or left of its indent. A list
        # frame closes at or left of its DASH indent for a key-line, but a dash
        # at exactly that indent is the next sibling item, so it must not close.
        while len(stack) > 1:
            frame_indent, _, kind = stack[-1]
            if kind == "list" and for_dash:
                if indent < frame_indent:
                    stack.pop()
                    continue
                break
            if indent <= frame_indent:
                stack.pop()
                continue
            break

    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        index += 1
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = _indent_of(raw_line)
        is_dash = stripped.startswith("- ") or stripped == "-"

        pop_to(indent, for_dash=is_dash)
        container = stack[-1][1]

        # ---- list item ----------------------------------------------------
        if is_dash:
            item_body = stripped[2:].strip() if stripped != "-" else ""
            if not isinstance(container, list):
                continue  # a stray dash with no owning key — skip, never guess
            if _DASH_MAPPING_KEY.match(item_body):
                # `- path: docs/handoff.md` opens a mapping item whose remaining
                # keys are indented further on the following lines. A scalar that
                # merely contains a colon (`- https://host/p`) does not.
                item: dict[str, Any] = {}
                container.append(item)
                key, _, value = item_body.partition(":")
                item[key.strip()] = _coerce(value)
                # Keys of this item sit right of the dash column.
                stack.append((indent + 1, item, "map"))
            else:
                container.append(_coerce(item_body))
            continue

        # ---- `key:` or `key: value` ---------------------------------------
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = _strip_comment(value).strip()
        if not isinstance(container, dict):
            continue

        if value.startswith("[") and value.endswith("]"):
            container[key] = _parse_flow_list(value)
        elif value:
            container[key] = _coerce(value)
        else:
            # Bare `key:` — a nested mapping or a block list, decided by the next
            # meaningful line. Peeking (rather than defaulting to {} and mutating
            # later) keeps the container type correct from the start.
            nxt = next(
                (
                    line
                    for line in lines[index:]
                    if line.strip() and not line.strip().startswith("#")
                ),
                None,
            )
            nxt_indent = _indent_of(nxt) if nxt is not None else -1
            nxt_is_dash = nxt is not None and (
                nxt.strip().startswith("- ") or nxt.strip() == "-"
            )
            if nxt_is_dash and nxt_indent >= indent:
                # A block list may sit at or right of its key's indent.
                # The frame records the DASH indent so sibling items survive.
                container[key] = []
                stack.append((nxt_indent, container[key], "list"))
            elif nxt is not None and nxt_indent > indent:
                container[key] = {}
                stack.append((indent, container[key], "map"))
            else:
                container[key] = None  # `key:` with nothing under it
    return root


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and parse the config. A relative path resolves against the repo root.

    Raises ``FileNotFoundError`` when absent — a script that needs config has
    nothing sane to fall back to.
    """
    target = Path(path)
    if not target.is_absolute():
        target = repo_root() / target
    if not target.is_file():
        raise FileNotFoundError(
            f"dev-model config not found: {target} (run ./init.sh, or pass an explicit path)"
        )
    return loads(target.read_text(encoding="utf-8"))


def get(config: dict[str, Any], dotted_key: str, default: Any = _MISSING) -> Any:
    """Look up a dotted key (``"review.bots"``) in a loaded config.

    Fail-loud (``KeyError``) when the key is missing and no ``default`` is given:
    a required key silently reading as ``None`` is how an engine ends up writing
    to the wrong path with no signal.
    """
    node: Any = config
    parts = dotted_key.split(".")
    for i, part in enumerate(parts):
        if not isinstance(node, dict) or part not in node:
            if default is not _MISSING:
                return default
            raise KeyError(
                f"required config key '{dotted_key}' not found "
                f"(missing at '{'.'.join(parts[: i + 1])}')"
            )
        node = node[part]
    return node


def resolve_path(config: dict[str, Any], dotted_key: str, *, root: Path | None = None) -> Path:
    """Resolve a config path value (``"paths.handoff"``) to an absolute ``Path``.

    A relative value resolves against the repo root (or ``root`` if given); an
    already-absolute value passes through unchanged.
    """
    value = get(config, dotted_key)
    candidate = Path(str(value))
    if candidate.is_absolute():
        return candidate
    return (root or repo_root()) / candidate


def get_str_list(config: dict[str, Any], dotted_key: str, default: list[str]) -> list[str]:
    """``get`` narrowed to a list of strings, tolerating a single scalar.

    Config lists are hand-authored, so a lone value written without brackets
    (``informational_checks: coderabbit``) is accepted as a one-item list rather
    than silently iterated character-by-character.
    """
    value = get(config, dotted_key, None)
    if value is None:
        return list(default)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return list(default)
