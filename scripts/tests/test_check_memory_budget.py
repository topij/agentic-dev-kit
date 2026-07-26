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


def test_default_memory_file_uses_repo_slug(monkeypatch, tmp_path):
    module = _load_module()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    resolved = module.default_memory_file()
    assert str(tmp_path) in str(resolved)
    assert resolved.name == "MEMORY.md"
    assert "memory" in resolved.parts


def test_rejects_non_positive_budgets(tmp_path):
    module = _load_module()
    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("fine\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        module.main(["--memory-file", str(memory_file), "--max-bytes", "0"])
