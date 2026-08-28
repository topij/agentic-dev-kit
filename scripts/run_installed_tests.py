#!/usr/bin/env python3
"""Run only kit test modules declared installed in an adopter manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath

import pytest


def _relative_engine_dir(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("engine directory must be a normalized repo-relative path")
    return path


def _declared_files(manifest_path: Path) -> set[PurePosixPath]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read install manifest {manifest_path}: {exc}") from exc
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, dict) or not all(isinstance(key, str) for key in files):
        raise ValueError("install manifest has no valid files map")
    declared: set[PurePosixPath] = set()
    for raw in files:
        path = PurePosixPath(raw)
        if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
            raise ValueError(f"install manifest contains an unsafe path: {raw}")
        declared.add(path)
    return declared


def installed_test_targets(root: Path, manifest_path: Path, engine_dir: str) -> list[Path]:
    """Return declared, present top-level pytest modules in the shipped test roots."""

    engine = _relative_engine_dir(engine_dir)
    manifest_test_roots = {
        PurePosixPath("scripts/tests"),
        PurePosixPath("scripts/lib/state_paths/tests"),
    }
    targets: list[Path] = []
    for rel in sorted(_declared_files(manifest_path), key=str):
        if (
            rel.parent not in manifest_test_roots
            or not rel.name.startswith("test_")
            or rel.suffix != ".py"
        ):
            continue
        installed_rel = engine.joinpath(*rel.parts[1:])
        candidate = root.joinpath(*installed_rel.parts)
        current = root
        for part in installed_rel.parts:
            current /= part
            if current.is_symlink():
                raise ValueError(
                    f"declared test path crosses a symlink after engine remapping: {rel}"
                )
        if not candidate.is_file():
            raise ValueError(
                f"declared test module is missing or not regular after engine remapping: {rel}"
            )
        targets.append(candidate)
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="adopter repository root")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="installed-state manifest (default: <root>/kit-manifest.json)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    manifest_path = args.manifest or (root / "kit-manifest.json")
    try:
        engine_dir = Path(__file__).resolve().parent.relative_to(root).as_posix()
        targets = installed_test_targets(root, manifest_path, engine_dir)
    except ValueError as exc:
        parser.error(str(exc))
    if not targets:
        print("kit tests: none declared installed — suite skipped")
        return 0
    print("kit tests:", *(str(path) for path in targets), sep="\n  ")
    return pytest.main([*(str(path) for path in targets), "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
