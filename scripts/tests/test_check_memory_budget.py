"""Tests for scripts/check_memory_budget.py — the Claude Code auto-memory tripwire.

Not required by the porting task, but added alongside it: the sibling
check_doc_budget.py has no dedicated suite either, so this at least pins the one
new script's core contract (warn-only by default, --strict flips exit code,
missing-file is a clean exit 2, not a traceback).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ENGINE_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ENGINE_DIR / "check_memory_budget.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_memory_budget_under_test", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec: the module's `@dataclass(frozen=True)` (combined with
    # `from __future__ import annotations`) resolves field annotations via
    # sys.modules[cls.__module__] at class-definition time, which requires the
    # module to already be registered — otherwise dataclass() raises AttributeError
    # on a None module lookup.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_evaluate_raises_when_file_missing(tmp_path):
    module = _load_module()
    with pytest.raises(FileNotFoundError):
        module.evaluate(tmp_path / "MEMORY.md")


def test_evaluate_under_budget_is_not_over(tmp_path):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("[a](a.md) - hook\n[b](b.md) - hook\n", encoding="utf-8")
    status = module.evaluate(memory_file, max_bytes=1000, max_line_chars=200)
    assert not status.over
    assert not status.over_size
    assert status.long_lines == []


def test_evaluate_over_byte_budget(tmp_path):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("x" * 500, encoding="utf-8")
    status = module.evaluate(memory_file, max_bytes=100, max_line_chars=200)
    assert status.over
    assert status.over_size


def test_evaluate_flags_long_lines(tmp_path):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("short\n" + ("y" * 250) + "\n", encoding="utf-8")
    status = module.evaluate(memory_file, max_bytes=100_000, max_line_chars=200)
    assert status.over
    assert not status.over_size
    assert status.long_lines == [(2, 250)]


def test_main_quiet_prints_nothing_under_budget(tmp_path, capsys):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("fine\n", encoding="utf-8")
    exit_code = module.main(["--memory-file", str(memory_file), "--quiet"])
    assert exit_code == 0
    assert capsys.readouterr().out == ""


def test_main_strict_exits_nonzero_when_over(tmp_path, capsys):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("x" * 500, encoding="utf-8")
    exit_code = module.main(["--memory-file", str(memory_file), "--max-bytes", "10", "--strict"])
    assert exit_code == 1


def test_main_without_strict_is_always_zero_even_when_over(tmp_path):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("x" * 500, encoding="utf-8")
    exit_code = module.main(["--memory-file", str(memory_file), "--max-bytes", "10"])
    assert exit_code == 0


def test_main_missing_file_exits_two(tmp_path):
    module = _load_module()
    exit_code = module.main(["--memory-file", str(tmp_path / "nope.md")])
    assert exit_code == 2


def test_main_json_output_shape(tmp_path, capsys):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("fine\n", encoding="utf-8")
    exit_code = module.main(["--memory-file", str(memory_file), "--json"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert '"over"' in out
    assert '"size_bytes"' in out


@pytest.mark.parametrize(("repo_path", "slug"), [
    ("/work/Alpha.dev_kit", "-work-Alpha-dev-kit"),
    ("/work/another project", "-work-another-project"),
])
def test_default_memory_file_uses_repo_slug(monkeypatch, tmp_path, repo_path, slug):
    module = _load_module()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(module, "REPO_ROOT", Path(repo_path))
    assert module.default_memory_file() == tmp_path / "projects" / slug / "memory" / "MEMORY.md"


def test_rejects_non_positive_budgets(tmp_path):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("fine\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        module.main(["--memory-file", str(memory_file), "--max-bytes", "0"])


@pytest.mark.parametrize("newline", [b"\n", b"\r\n", b"\r"])
def test_byte_budget_measures_stored_newlines(tmp_path, capsys, newline):
    """The byte budget measures the file while line lengths exclude terminators."""
    import json

    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    payload = newline.join(["café".encode("utf-8"), b"next", b""])
    memory_file.write_bytes(payload)
    status = module.evaluate(memory_file, max_bytes=len(payload) - 1, max_line_chars=4)
    assert status.size_bytes == len(payload)
    assert status.line_count == 2 and status.long_lines == []
    assert status.over_size and status.over
    assert module.main([
        "--memory-file", str(memory_file), "--max-bytes", str(len(payload) - 1),
        "--max-line-chars", "4", "--strict", "--json",
    ]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["size_bytes"] == len(payload) and report["over_size"]
    assert module.main([
        "--memory-file", str(memory_file), "--max-bytes", str(len(payload)),
        "--max-line-chars", "4", "--strict", "--json",
    ]) == 0
    assert not json.loads(capsys.readouterr().out)["over"]
