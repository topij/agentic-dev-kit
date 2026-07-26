#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Report how far an adopting repo has drifted from the kit it was installed from.

The upgrade problem this exists to solve: an adopter's copy of the kit has no
version marker on its *engines* and no record of whether they were edited. Real
installs surveyed before this was written spanned four shapes — an ancestor with
no config surface at all, a v1-schema repo with only two of six engines and a
`paths.engines` value that pointed at the wrong directory, a correctly namespaced
v2 repo, and the template itself — and nothing could tell them apart. One repo's
``pr_watch.py`` was three features behind upstream and nobody knew.

So: **engines are kit-owned, config is adopter-owned.** That invariant is what
makes an upgrade a file copy instead of a manual merge, and this script is what
verifies it still holds. Per kit-owned file it reports one of:

``unchanged``
    Byte-identical to the manifest. Safe to replace outright on upgrade.
``differs``
    Present but not byte-identical to the manifest. A hash mismatch cannot
    distinguish "older kit version" from "hand-edited", so this deliberately
    does NOT claim which — calling an old file "locally modified" sends someone
    hunting for edits they never made. The report narrows it using the config's
    schema version, and either way the required action is the same: diff before
    replacing, never clobber.
``missing``
    Not installed. Either a deliberately sized-down adoption or an incomplete
    one; the report can't tell, so it says so rather than guessing.
``unknown-version``
    The manifest has no entry for this file, so drift can't be judged.

Adopter-owned paths (the config, the narrative docs) are **never** compared —
they are supposed to differ, and reporting them as drift would bury the signal.

`paths.engines` indirection is handled: the manifest records the kit's own
layout (``scripts/…``), and comparison maps that prefix onto whatever the
adopter configured, so a repo that vendored engines under ``scripts/devkit/``
compares correctly without a rewritten manifest.

Read-only. Never writes to the repo it inspects (``--generate-manifest`` writes
only the manifest, and only when run in the kit's own checkout).

Usage:
    uv run scripts/kit_doctor.py                    # human report
    uv run scripts/kit_doctor.py --json             # machine-readable
    uv run scripts/kit_doctor.py --generate-manifest  # (kit repo) refresh the manifest

Exit codes:
    0 — every kit-owned file is `unchanged` (or intentionally absent)
    1 — at least one file `differs` or is `unknown-version`
    2 — usage error (no config, no manifest, unreadable input)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from kitconfig import get, load_config, repo_root  # noqa: E402

MANIFEST_NAME = "kit-manifest.json"

# Files the KIT owns, as they sit in the kit's own tree. An adopter should never
# need to edit one of these — everything project-specific belongs in
# config/dev-model.yaml. `role` groups the report; `engine_relative` marks the
# paths that move with `paths.engines`.
KIT_OWNED: tuple[tuple[str, str], ...] = (
    # engines (move with paths.engines)
    ("scripts/pr_watch.py", "engine"),
    ("scripts/check_doc_budget.py", "engine"),
    ("scripts/archive_plan_sessions.py", "engine"),
    ("scripts/dev_session.sh", "engine"),
    ("scripts/reconcile_sessions.sh", "engine"),
    ("scripts/kit_doctor.py", "engine"),
    ("scripts/lib/kitconfig.py", "engine"),
    ("scripts/lib/devmodel_config.py", "engine"),
    ("scripts/lib/repo_root.sh", "engine"),
    ("scripts/lib/state_paths/__init__.py", "engine"),
    ("scripts/lib/state_paths/resolver.py", "engine"),
    ("scripts/lib/state_paths/paths.py", "engine"),
    ("scripts/lib/state_paths/repo_root.py", "engine"),
    ("scripts/hooks/pre-push", "hook"),
    # shared workflow definitions
    ("docs/agentic-dev-kit/workflows/session-start.md", "workflow"),
    ("docs/agentic-dev-kit/workflows/wrap-up.md", "workflow"),
    ("docs/agentic-dev-kit/workflows/pr-watch.md", "workflow"),
    ("docs/agentic-dev-kit/workflows/parallel.md", "workflow"),
    ("docs/agentic-dev-kit/safety-critical-changes.md", "doctrine"),
    # Tracked because safety-critical-changes.md — which IS refreshed by
    # /upgrade — links to it from rules 2 and 3. An untracked target means an
    # upgrading adopter gets doctrine pointing at a file they do not have, and
    # kit_doctor cannot report it missing because it is not tracked.
    ("docs/agentic-dev-kit/fallback-review-panel.md", "doctrine"),
    # Tracked so an adopter who installs the kit gets it, and so kit_doctor can
    # say when they did not. NOT for the same reason as the line above, despite
    # an earlier version of this comment claiming so: fallback-review-panel.md
    # is linked from safety-critical-changes.md, which is itself manifest-owned
    # and /upgrade-refreshed, so an untracked target would leave *shipped*
    # doctrine dangling. This file's referrers (/adopt, ruff.toml, the ruff CI
    # step) are none of them manifest-owned, so nothing shipped would dangle —
    # the argument for tracking it is simply that it is doctrine an adopter
    # needs, and it is the only surface that explains the engines-dir exclusion.
    # (/upgrade does not mention it at all; the earlier comment said it did.)
    ("docs/agentic-dev-kit/adopting-into-a-linted-repo.md", "doctrine"),
    # narrative-doc templates (the rendered outputs are adopter-owned)
    ("docs/templates/handoff.md.tmpl", "template"),
    ("docs/templates/handoff-history.md.tmpl", "template"),
    ("docs/templates/friction-log.md.tmpl", "template"),
    ("docs/templates/friction-log-archive.md.tmpl", "template"),
)

# Paths that are the ADOPTER's — expected to differ, never reported as drift.
# Listed explicitly (rather than inferred) so the boundary is auditable, and so
# an installer can consume the same list to decide what not to copy.
ADOPTER_OWNED: tuple[str, ...] = (
    "config/dev-model.yaml",
    "docs/handoff.md",
    "docs/handoff-history.md",
    "docs/friction-log.md",
    "docs/friction-log-archive.md",
    # This repo's own narrative files (see the note in config/dev-model.yaml).
    "docs/kit-handoff.md",
    "docs/kit-handoff-history.md",
    "docs/kit-friction-log.md",
    "docs/kit-friction-log-archive.md",
    "README.md",
    ".gitignore",
)

# `paths.engines` default in the kit's own layout — the prefix remapped onto an
# adopter's configured engines directory.
KIT_ENGINE_PREFIX = "scripts"

# Engine filenames as they sit UNDER `paths.engines`, used to probe whether a
# configured engines directory holds anything at all. DERIVED from KIT_OWNED
# rather than restated: this used to be a hardcoded triple (check_doc_budget.py,
# pr_watch.py, dev_session.sh), so a deliberately sized-down install containing
# only kit_doctor.py and lib/kitconfig.py reported "contains no kit engine" —
# from inside the very directory it was executing out of, while the same run
# counted those two files as `unchanged` (issue #59).
#
# The class is NOT closed by this. `init.sh` carries the identical triple in
# `detect_engines_dir()`, where the same bug does real damage rather than
# merely misreporting: on this exact fixture it writes `engines: scripts` for a
# tree whose engines live in `scripts/devkit`. That is filed separately. #47
# tracks deriving KIT_OWNED itself from the shipped tree, which subsumes both.
_ENGINE_NAMES: tuple[str, ...] = tuple(
    rel[len(KIT_ENGINE_PREFIX) + 1 :]
    for rel, role in KIT_OWNED
    if role == "engine" and rel.startswith(KIT_ENGINE_PREFIX + "/")
)


@dataclass
class FileStatus:
    path: str
    role: str
    state: str
    detail: str = ""


@dataclass
class Report:
    kit_version_config: int | None
    kit_version_manifest: int | None
    engines_dir: str
    engines_dir_ok: bool
    hooks_installed: bool
    narrative_rendered: dict[str, bool]
    # The version values as they were actually written, kept ONLY so the report
    # can tell "no version key at all" (pre-v2, migrate) apart from "a version
    # key that is not a number" (a typo, do not migrate). Both leave the parsed
    # field at None; conflating them would send an adopter with `version: v2`
    # to run a migration they do not need.
    #
    # BOTH sides are carried. Keeping the raw config value and not the manifest
    # one made an unreadable manifest version fall through to a bare `✓ config
    # schema: vN` — a checkmark for a comparison that could not be performed,
    # which is the same "assert a cause it cannot know" failure the config side
    # added this field to prevent.
    kit_version_config_raw: object = None
    kit_version_manifest_raw: object = None
    files: list[FileStatus] = field(default_factory=list)

    @property
    def drifted(self) -> list[FileStatus]:
        return [f for f in self.files if f.state in ("differs", "unknown-version")]

    @property
    def missing(self) -> list[FileStatus]:
        return [f for f in self.files if f.state == "missing"]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_version(value: object) -> int | None:
    """Read a schema version from config or manifest; None if it isn't one.

    ``kitconfig`` coerces UNQUOTED integers only — deliberately, because that is
    what PyYAML does — so ``version: "2"`` arrives here as the string ``"2"``
    and the ``cfg_v < man_v`` comparison in `render` raised ``TypeError: '<' not
    supported between instances of 'str' and 'int'`` (issue #61). Quoting a
    scalar is an ordinary thing for a YAML author to do, and a *read-only
    diagnostic* answering it with a traceback tells the adopter the doctor is
    broken rather than their config. Coercing here rather than in ``kitconfig``
    keeps that module's PyYAML parity intact — the divergence would be the bug.

    Dispatched on type rather than run through ``int(str(value))``, because that
    shorter form is *looser* than "a schema version" in two directions a review
    panel demonstrated: ``int()`` accepts Python's underscore separators, so
    ``version: "1_0"`` became a confident, silent **10**, and it accepts any
    Unicode decimal digit, so ``version: "２"`` became 2. Both then flowed into
    ``--generate-manifest`` and would have been stamped.

    ``bool`` is rejected first and explicitly: it is an ``int`` subclass, so the
    ``isinstance(value, int)`` branch below would otherwise read ``version:
    true`` as schema v1.

    A ``float`` that is integral is accepted (``2.0`` → 2) only because the code
    this replaced handled it and rejecting it would make a plausible YAML
    spelling strictly worse than before the fix.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        text = value.strip()
        # `isascii()` rejects Unicode decimal digits; `isdigit()` rejects the
        # `1_0` underscore form that bare `int()` would silently accept.
        return int(text) if text.isascii() and text.isdigit() else None
    return None


def _hook_dirs(root: Path):
    """Every directory git might read hooks from, honoring ``core.hooksPath``.

    ``$GIT_DIR/hooks`` is not the only answer: ``core.hooksPath`` overrides it,
    and pre-commit plus several monorepo layouts set it. Checking only
    ``.git/hooks`` reports a correctly-installed hook as missing — the same
    mistake ``init.sh`` made when *writing* the shim, so it would have told an
    adopter to re-run an install that had already worked.

    Read via a plain config-file scan rather than shelling out to ``git``, so
    this stays import- and subprocess-free.

    **Known-incomplete, deliberately (issue #61).** This scan sees only
    ``.git/config``, so a ``hooksPath`` set in ``~/.gitconfig``, under
    ``$XDG_CONFIG_HOME``, or via ``[includeIf]`` still reads as "NOT installed",
    and it does not apply git's own value normalization (surrounding quotes,
    inline ``#``/``;`` comments, ``~`` expansion). Asking git instead is the
    obvious fix and was attempted here; a review panel found it traded these
    false negatives for a worse set — answering from an *enclosing* repository
    when `root` is not one, honoring an inherited ``GIT_DIR``, and reporting a
    hook installed at ``.git/hooks`` as present when ``core.hooksPath`` sends
    git elsewhere. Reverted rather than shipped half-right; the issue carries
    the evidence and the shape a correct version needs.
    """
    candidates: list[Path] = []
    config = root / ".git" / "config"
    if config.is_file():
        for line in config.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("hooksPath"):
                _, _, value = stripped.partition("=")
                value = value.strip()
                if value:
                    path = Path(value)
                    candidates.append(path if path.is_absolute() else root / path)
    candidates.append(root / ".git" / "hooks")
    return [c / "pre-push" for c in candidates]


def _remap(rel: str, engines_dir: str) -> str:
    """Rewrite a kit-layout path onto the adopter's engines directory."""
    engines_dir = engines_dir.rstrip("/") or KIT_ENGINE_PREFIX
    if engines_dir == KIT_ENGINE_PREFIX:
        return rel
    if rel == KIT_ENGINE_PREFIX or rel.startswith(KIT_ENGINE_PREFIX + "/"):
        return engines_dir + rel[len(KIT_ENGINE_PREFIX) :]
    return rel


def generate_manifest(root: Path, kit_version: int) -> dict:
    """Hash every kit-owned file in the kit's own checkout.

    Run in the kit repo at release time. A file listed in ``KIT_OWNED`` but
    absent here is recorded as ``None`` rather than skipped, so a packaging
    mistake shows up as an explicit hole instead of silently narrowing what
    later gets checked.
    """
    files: dict[str, dict] = {}
    for rel, role in KIT_OWNED:
        target = root / rel
        files[rel] = {
            "sha256": sha256_of(target) if target.is_file() else None,
            "role": role,
        }
    return {
        "kit_version": kit_version,
        "files": files,
        "adopter_owned": list(ADOPTER_OWNED),
    }


def inspect(root: Path, manifest: dict, config: dict) -> Report:
    engines_dir = str(get(config, "paths.engines", KIT_ENGINE_PREFIX))
    manifest_files = manifest.get("files") or {}

    statuses: list[FileStatus] = []
    for rel, role in KIT_OWNED:
        local_rel = _remap(rel, engines_dir)
        target = root / local_rel
        entry = manifest_files.get(rel) or {}
        expected = entry.get("sha256")
        if not target.is_file():
            statuses.append(FileStatus(local_rel, role, "missing"))
            continue
        if expected is None:
            statuses.append(
                FileStatus(local_rel, role, "unknown-version", "no manifest entry")
            )
            continue
        actual = sha256_of(target)
        if actual == expected:
            statuses.append(FileStatus(local_rel, role, "unchanged"))
        else:
            statuses.append(
                FileStatus(local_rel, role, "differs", f"{actual[:12]} != {expected[:12]}")
            )

    # A configured engines dir that holds no engine is the silent failure that
    # made one surveyed repo's workflows resolve `<engine-dir>/…` to nothing.
    # ANY kit engine counts (see `_ENGINE_NAMES`): a sized-down adoption is a
    # supported state, so the probe must answer "is this the engines dir?" and
    # not "did you install the three I happen to name?".
    engines_probe = any((root / engines_dir / name).is_file() for name in _ENGINE_NAMES)

    hook_target = root / engines_dir / "hooks" / "pre-push"
    hooks_installed = hook_target.is_file() and any(
        candidate.is_file() for candidate in _hook_dirs(root)
    )

    narrative: dict[str, bool] = {}
    for key in ("paths.handoff", "paths.friction_log"):
        rel = get(config, key, None)
        if not rel:
            continue
        doc = root / str(rel)
        # "Rendered" = present and no longer carrying the shipped marker.
        narrative[str(rel)] = doc.is_file() and (
            "devkit-template: unrendered" not in doc.read_text(encoding="utf-8", errors="replace")
        )

    raw_version = get(config, "kit.version", None)
    raw_manifest_version = manifest.get("kit_version")
    return Report(
        kit_version_config=_as_version(raw_version),
        kit_version_manifest=_as_version(raw_manifest_version),
        kit_version_config_raw=raw_version,
        kit_version_manifest_raw=raw_manifest_version,
        engines_dir=engines_dir,
        engines_dir_ok=engines_probe,
        hooks_installed=hooks_installed,
        narrative_rendered=narrative,
        files=statuses,
    )


def render(report: Report) -> str:
    lines: list[str] = ["kit-doctor — installation report", ""]
    cfg_v, man_v = report.kit_version_config, report.kit_version_manifest
    if cfg_v is None and report.kit_version_config_raw is not None:
        # Present but not a number. Deliberately NOT the "run ./init.sh to
        # migrate" advice below: the fix is a one-character config edit, and
        # sending someone into a migration for a typo is the same wrong-advice
        # failure as the engines probe in #59.
        lines.append(
            f"  ⚠ config schema: UNREADABLE — kit.version is {report.kit_version_config_raw!r}, "
            "expected an unquoted or quoted integer (e.g. `version: 2`)"
        )
    elif cfg_v is None:
        lines.append("  ⚠ config schema: UNVERSIONED (pre-v2) — run ./init.sh to migrate and stamp")
    elif man_v is None and report.kit_version_manifest_raw is not None:
        # The manifest's own version is unreadable, so there is nothing to
        # compare against. Say that instead of printing a bare ✓, which would
        # be a checkmark for a comparison that never ran.
        lines.append(
            f"  ⚠ config schema: v{cfg_v}, but the manifest's kit_version is "
            f"{report.kit_version_manifest_raw!r} — cannot tell whether this config is behind"
        )
    elif man_v is not None and cfg_v < man_v:
        lines.append(f"  ⚠ config schema: v{cfg_v}, kit ships v{man_v} — run ./init.sh to migrate")
    else:
        lines.append(f"  ✓ config schema: v{cfg_v}")

    if report.engines_dir_ok:
        lines.append(f"  ✓ paths.engines: {report.engines_dir}")
    else:
        lines.append(
            f"  ✗ paths.engines: {report.engines_dir} — contains no kit engine. "
            "Every workflow's <engine-dir>/… reference resolves to nothing."
        )

    lines.append(
        f"  {'✓' if report.hooks_installed else '⚠'} pre-push hook: "
        + ("installed" if report.hooks_installed else "NOT installed — run ./init.sh")
    )
    for doc, rendered in report.narrative_rendered.items():
        lines.append(
            f"  {'✓' if rendered else '⚠'} {doc}: "
            + ("in use" if rendered else "still an unrendered template — run ./init.sh")
        )

    by_state: dict[str, list[FileStatus]] = {}
    for f in report.files:
        by_state.setdefault(f.state, []).append(f)

    lines.append("")
    lines.append(
        f"  files: {len(by_state.get('unchanged', []))} unchanged, "
        f"{len(by_state.get('differs', []))} differ, "
        f"{len(by_state.get('missing', []))} missing, "
        f"{len(by_state.get('unknown-version', []))} unknown"
    )
    # Narrow "differs" using the schema version rather than asserting a cause.
    # An UNREADABLE version narrows nothing: "no version key" soundly implies
    # pre-v2 and therefore older, but `version: v2` implies nothing at all, and
    # this file's whole position on `differs` is that it must not claim a cause
    # it cannot know.
    # EITHER side being present-but-unparseable makes the comparison unusable.
    unreadable_version = (
        report.kit_version_config is None and report.kit_version_config_raw is not None
    ) or (report.kit_version_manifest is None and report.kit_version_manifest_raw is not None)
    # `behind` has THREE consumers: the `elif` below, the `else` below, and the
    # kit-bug nudge after this block. It is deliberately not re-qualified by
    # `unreadable_version` — each consumer handles that itself, and a redundant
    # condition here would pin nothing while reading as if it did.
    behind = (
        report.kit_version_config is not None
        and report.kit_version_manifest is not None
        and report.kit_version_config < report.kit_version_manifest
    ) or report.kit_version_config is None
    if unreadable_version:
        differs_label = (
            "differ from the manifest — a schema version is unreadable, so it "
            "cannot narrow this to an older kit versus local edits; diff before replacing"
        )
    elif behind:
        differs_label = (
            "differ from the manifest — this repo's config predates the kit's, so these are "
            "probably just an OLDER version rather than local edits; diff to confirm"
        )
    else:
        differs_label = (
            "differ from the manifest — same schema version, so these are likely LOCAL EDITS; "
            "diff before replacing"
        )
    for state, label in (
        ("differs", differs_label),
        ("unknown-version", "no manifest entry — drift cannot be judged"),
        ("missing", "not installed (sized-down adoption, or incomplete)"),
    ):
        items = by_state.get(state) or []
        if not items:
            continue
        lines.append(f"\n  {label}:")
        for f in items:
            suffix = f"  ({f.detail})" if f.detail else ""
            lines.append(f"    · {f.path} [{f.role}]{suffix}")

    # `not unreadable_version` is load-bearing, and only for the MANIFEST side:
    # an unreadable *config* version leaves `behind` True and is suppressed by
    # that alone, but an unreadable *manifest* version leaves `behind` False, so
    # without this the nudge would fire on a comparison that never ran.
    if by_state.get("differs") and not behind and not unreadable_version:
        lines.append(
            "\n  Engines are kit-owned: everything project-specific belongs in"
            "\n  config/dev-model.yaml. If you had to edit an engine to adopt it,"
            "\n  that is a kit bug — please report it rather than carrying the patch."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report kit installation drift.")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--generate-manifest",
        action="store_true",
        help="(kit repo only) hash every kit-owned file and write kit-manifest.json",
    )
    parser.add_argument("--root", type=Path, default=None, help="repo root (default: discovered)")
    parser.add_argument("--manifest", type=Path, default=None, help="path to kit-manifest.json")
    args = parser.parse_args(argv)

    root = (args.root or repo_root()).resolve()
    manifest_path = args.manifest or (root / MANIFEST_NAME)

    try:
        config = load_config(root / "config" / "dev-model.yaml")
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "hint: a repo with no config/dev-model.yaml predates the config surface "
            "entirely — adopt it with the /adopt skill rather than upgrading.",
            file=sys.stderr,
        )
        return 2

    if args.generate_manifest:
        raw_version = get(config, "kit.version", 2)
        version = _as_version(raw_version)
        if version is None:
            # Refuse rather than guess: a manifest stamped with the wrong
            # kit_version misreports drift for every adopter that reads it.
            print(
                f"error: kit.version is {raw_version!r}, expected an integer — "
                "refusing to stamp a manifest with a guessed version",
                file=sys.stderr,
            )
            return 2
        manifest = generate_manifest(root, version)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        holes = [p for p, e in manifest["files"].items() if e["sha256"] is None]
        print(f"wrote {manifest_path} ({len(manifest['files'])} files, kit_version={version})")
        if holes:
            print(f"warning: {len(holes)} listed file(s) absent from this checkout:", file=sys.stderr)
            for h in holes:
                print(f"  · {h}", file=sys.stderr)
        return 0

    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        print(
            "hint: copy kit-manifest.json in from the kit release you are comparing against.",
            file=sys.stderr,
        )
        return 2
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"error: unreadable manifest {manifest_path}: {exc}", file=sys.stderr)
        return 2

    report = inspect(root, manifest, config)

    if args.json:
        print(
            json.dumps(
                {
                    "kit_version_config": report.kit_version_config,
                    "kit_version_manifest": report.kit_version_manifest,
                    # A null parsed value with a non-null raw one means the key
                    # is present but unreadable, which a consumer cannot
                    # otherwise distinguish from an absent version.
                    "kit_version_config_raw": report.kit_version_config_raw,
                    "kit_version_manifest_raw": report.kit_version_manifest_raw,
                    "engines_dir": report.engines_dir,
                    "engines_dir_ok": report.engines_dir_ok,
                    "hooks_installed": report.hooks_installed,
                    "narrative_rendered": report.narrative_rendered,
                    "files": [
                        {"path": f.path, "role": f.role, "state": f.state, "detail": f.detail}
                        for f in report.files
                    ],
                },
                indent=1,
            )
        )
    else:
        print(render(report))

    return 1 if report.drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
