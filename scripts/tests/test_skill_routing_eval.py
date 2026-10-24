"""The deterministic skill-routing check (#1221): descriptions against case prompts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

ENGINE_DIR = engine_dir(Path(__file__))
REPO_ROOT = find_repo_root(ENGINE_DIR)
ENGINE = ENGINE_DIR / "skill_routing_eval.py"
CASES = REPO_ROOT / "docs" / "agentic-dev-kit" / "skill-routing" / "cases.json"
sys.path.insert(0, str(ENGINE_DIR))

import skill_routing_eval  # noqa: E402

SLUGS = skill_routing_eval.model_invoked_slugs()


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, str(ENGINE), *args], capture_output=True, text=True, check=False
    )


def _copy_adapters(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for template in skill_routing_eval.ADAPTER_PATHS.values():
        for slug in SLUGS:
            rel = template.format(slug=slug)
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, root / rel)
    return root


def _set_description(root: Path, slug: str, description: str) -> None:
    for template in skill_routing_eval.ADAPTER_PATHS.values():
        path = root / template.format(slug=slug)
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        index = next(i for i, line in enumerate(lines) if line.startswith("description:"))
        lines[index] = f"description: {description}\n"
        path.write_text("".join(lines), encoding="utf-8")


def _cases(tmp_path: Path, mutate=None) -> Path:
    data = json.loads(CASES.read_text(encoding="utf-8"))
    if mutate:
        mutate(data)
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_the_kits_own_descriptions_route_every_case() -> None:
    result = _run("--root", str(REPO_ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 failure(s)" in result.stdout


def test_every_model_invoked_skill_has_positive_and_negative_cases() -> None:
    skills = json.loads(CASES.read_text(encoding="utf-8"))["skills"]
    assert sorted(skills) == sorted(SLUGS)
    for slug in SLUGS:
        assert skills[slug]["positive"], slug
        assert any("owner" in case for case in skills[slug]["negative"]), slug
        assert any("owner" not in case for case in skills[slug]["negative"]), slug


def test_a_description_that_loses_its_vocabulary_fails(tmp_path: Path) -> None:
    root = _copy_adapters(tmp_path)
    _set_description(root, "wrap-up", "Perform the closing procedure described in the shared workflow document.")
    result = _run("--root", str(root), "--cases", str(_cases(tmp_path)))
    assert result.returncode == 1, result.stdout
    assert "positive prompt for wrap-up" in result.stdout
    # Both runtimes are scored from their own adapter.
    assert "claude: positive prompt for wrap-up" in result.stdout
    assert "codex: positive prompt for wrap-up" in result.stdout


def test_one_runtimes_weakened_adapter_fails_on_its_own(tmp_path: Path) -> None:
    root = _copy_adapters(tmp_path)
    path = root / skill_routing_eval.ADAPTER_PATHS["codex"].format(slug="pr-watch")
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    index = next(i for i, line in enumerate(lines) if line.startswith("description:"))
    lines[index] = "description: Run the shared procedure.\n"
    path.write_text("".join(lines), encoding="utf-8")
    result = _run("--root", str(root), "--cases", str(_cases(tmp_path)))
    assert result.returncode == 1, result.stdout
    assert "codex: positive prompt for pr-watch" in result.stdout
    assert "claude: positive prompt for pr-watch" not in result.stdout


def test_two_descriptions_that_say_the_same_thing_collide(tmp_path: Path) -> None:
    root = _copy_adapters(tmp_path)
    text = (REPO_ROOT / ".claude/skills/session-start/SKILL.md").read_text(encoding="utf-8")
    description = next(line for line in text.splitlines() if line.startswith("description:")).split(":", 1)[1].strip()
    _set_description(root, "wrap-up", description)
    result = _run("--root", str(root), "--cases", str(_cases(tmp_path)))
    assert result.returncode == 1
    assert "descriptions of session-start and wrap-up collide" in result.stdout


def test_a_negative_prompt_the_skill_outranks_its_owner_on_fails(tmp_path: Path) -> None:
    def mutate(data: dict) -> None:
        data["skills"]["wrap-up"]["negative"].append(
            {"prompt": "Wrap up the session and record what shipped in the handoff", "owner": "pr-watch"}
        )

    result = _run("--root", str(REPO_ROOT), "--cases", str(_cases(tmp_path, mutate)))
    assert result.returncode == 1
    assert "negative prompt for wrap-up not rejected" in result.stdout
    assert "owner pr-watch" in result.stdout


def test_an_unrelated_prompt_that_scores_too_high_fails(tmp_path: Path) -> None:
    def mutate(data: dict) -> None:
        data["skills"]["parallel"]["negative"].append({"prompt": "Plan the isolated development lanes in worktrees"})

    result = _run("--root", str(REPO_ROOT), "--cases", str(_cases(tmp_path, mutate)))
    assert result.returncode == 1
    assert "unrelated_max_score" in result.stdout


def test_cases_must_cover_exactly_the_model_invoked_skills(tmp_path: Path) -> None:
    def mutate(data: dict) -> None:
        data["skills"].pop("parallel")
        data["skills"]["upgrade"] = {"positive": [{"prompt": "upgrade the kit"}], "negative": []}

    result = _run("--root", str(REPO_ROOT), "--cases", str(_cases(tmp_path, mutate)))
    assert result.returncode == 1
    assert "parallel: no cases" in result.stdout
    assert "upgrade: has cases but is not a model-invoked skill" in result.stdout


def test_an_unreadable_case_file_or_adapter_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"settings": {"top_k": "one"}, "skills": {}}', encoding="utf-8")
    result = _run("--root", str(REPO_ROOT), "--cases", str(bad))
    assert result.returncode == 2
    assert "settings.top_k must be a number" in result.stderr

    empty = tmp_path / "empty"
    empty.mkdir()
    result = _run("--root", str(empty), "--cases", str(CASES))
    assert result.returncode == 2
    assert "cannot read adapter" in result.stderr


def test_stemming_joins_the_forms_a_request_uses() -> None:
    assert skill_routing_eval.tokens("watching watched watches") == ["watch"] * 3
    assert skill_routing_eval.tokens("the PR is green") == ["pr", "green"]
