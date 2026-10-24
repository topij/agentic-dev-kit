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


def _tie_model() -> skill_routing_eval.Model:
    return skill_routing_eval.Model.build({"a-skill": "foo bar", "z-skill": "foo bar"})


def test_a_tie_fails_a_positive_case_whichever_slug_sorts_first(tmp_path: Path, monkeypatch) -> None:
    """Two skills scoring the same on a prompt: neither is ahead, so neither passes top_k 1."""
    monkeypatch.setattr(skill_routing_eval, "model_invoked_slugs", lambda: ("a-skill", "z-skill"))
    model = _tie_model()
    monkeypatch.setattr(skill_routing_eval.Model, "build", classmethod(lambda cls, d: model))
    monkeypatch.setattr(skill_routing_eval, "read_descriptions", lambda root, runtime: {})
    cases = {
        "settings": {"top_k": 1, "unrelated_max_score": 0.9, "collision_threshold": 1.1},
        "skills": {
            slug: {"positive": [{"prompt": "foo"}], "negative": [{"prompt": "qux", "owner": other}, {"prompt": "qux"}]}
            for slug, other in (("a-skill", "z-skill"), ("z-skill", "a-skill"))
        },
    }
    failures = skill_routing_eval.evaluate(tmp_path, cases).failures
    assert any("positive prompt for a-skill" in f for f in failures), failures
    assert any("positive prompt for z-skill" in f for f in failures), failures


def test_a_prompt_sharing_no_word_with_any_description_passes_nothing(tmp_path: Path) -> None:
    def mutate(data: dict) -> None:
        data["skills"]["parallel"]["positive"].append({"prompt": "zzzz qqqq"})
        # Both score 0: an owner that does not outscore the skill does not reject it.
        data["skills"]["wrap-up"]["negative"].append({"prompt": "zzzz qqqq", "owner": "pr-watch"})

    result = _run("--root", str(REPO_ROOT), "--cases", str(_cases(tmp_path, mutate)))
    assert result.returncode == 1
    assert "positive prompt for parallel" in result.stdout
    assert "negative prompt for wrap-up not rejected" in result.stdout


def test_a_collision_just_over_the_threshold_fails(tmp_path: Path) -> None:
    def mutate(data: dict) -> None:
        data["settings"]["collision_threshold"] = 0.05

    result = _run("--root", str(REPO_ROOT), "--cases", str(_cases(tmp_path, mutate)))
    assert result.returncode == 1
    assert "collide (cosine" in result.stdout


def test_empty_case_lists_fail(tmp_path: Path) -> None:
    def mutate(data: dict) -> None:
        data["skills"]["pr-watch"] = {"positive": [], "negative": []}

    result = _run("--root", str(REPO_ROOT), "--cases", str(_cases(tmp_path, mutate)))
    assert result.returncode == 1
    assert "pr-watch: no positive prompts" in result.stdout
    assert "pr-watch: no negative prompt owned by another skill" in result.stdout
    assert "pr-watch: no negative prompt that no kit skill should take" in result.stdout


def test_a_malformed_case_exits_2(tmp_path: Path) -> None:
    for mutate, message in (
        (lambda d: d["skills"]["pr-watch"]["positive"].append({"text": "x"}), "needs a non-empty 'prompt'"),
        (lambda d: d["skills"]["pr-watch"].update(positive="watch my pr"), "must be a list"),
        (lambda d: d["skills"]["pr-watch"]["negative"].append({"prompt": "x", "owner": "nope"}), "has owner 'nope'"),
        (lambda d: d["skills"]["pr-watch"]["negative"].append({"prompt": "x", "owner": "pr-watch"}), "has owner 'pr-watch'"),
    ):
        result = _run("--root", str(REPO_ROOT), "--cases", str(_cases(tmp_path, mutate)))
        assert result.returncode == 2, (message, result.stdout, result.stderr)
        assert message in result.stderr
        assert "Traceback" not in result.stderr
