"""Exercise the narrative preflight against independent committed Git fixtures."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from _repo_layout import engine_dir
from conftest import require_kit_paths

ENGINE = engine_dir(Path(__file__)) / "check_record_prose.py"
LOCAL_REF = "#7"
FOREIGN_REF = "other/repo#7"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True).stdout.strip()


def save(root: Path, path: str, text: str) -> None:
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def commit(root: Path, message: str = "narrative update") -> str:
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "test")
    git(root, "config", "user.email", "test@example.com")
    save(root, "config/dev-model.yaml", """paths:
  handoff: docs/plan.md
  handoff_history: docs/history.md
  friction_log: docs/inbox.md
  friction_log_archive: docs/archive.md
doc_budgets:
  - path: docs/plan.md
    budget: 20
"""
    )
    save(root, "docs/plan.md", "# Plan\n\nEarlier record.\n")
    save(root, "docs/history.md", "# History\n")
    save(root, "docs/target with space.md", "# Target\n")
    return root, commit(root, "baseline")


def run(repo: tuple[Path, str], head: str, *extra: str) -> tuple[int, dict]:
    require_kit_paths("scripts/check_record_prose.py")
    root, base = repo
    result = subprocess.run(
        ["uv", "run", str(ENGINE), "--root", str(root), "--base", base,
         "--head", head, "--json", *extra],
        capture_output=True, text=True, timeout=90,
    )
    assert result.stdout, result.stderr
    report = json.loads(result.stdout)
    assert {"status", "findings", "unavailable", "stamps", "limits"} <= report.keys(), report
    assert all(isinstance(report[field], list) for field in ("findings", "unavailable", "stamps", "limits"))
    return result.returncode, report


def test_committed_snapshot_ignores_dirty_files_and_has_no_write(repo):
    root, base = repo
    save(root, "docs/plan.md", f"# Plan\n\n`make test` at `{base}` on 2026-10-10 printed a result.\n\n"
         "[Target](<target with space.md>) and [external](https://example.com).\n\n"
         "`[example](missing.md)`\n")
    head = commit(root)
    save(root, "docs/plan.md", "dirty working copy\n" * 100)
    before = git(root, "status", "--porcelain=v1")
    code, report = run(repo, head)
    assert code == 0, report
    assert report["status"] == "passed"
    assert report["stamps"][0]["revision"] == base
    assert report["stamps"][0]["names_head"] is False
    assert report["limits"]
    assert git(root, "status", "--porcelain=v1") == before
    assert (root / "docs/plan.md").read_text() == "dirty working copy\n" * 100


@pytest.mark.parametrize("text,kind", [
    ("line\n" * 21, "budgets"),
    ("[Missing](missing.md)\n", "links"),
    (f"Not `fixes {LOCAL_REF}`.\n", "closing-keywords"),
    (f"fixes\n{LOCAL_REF}\n", "closing-keywords"),
    ("`make test` at `HEAD` on 2026-10-10 printed a result.\n", "stamps"),
    ("`make test` at `abcdef0` on 2026-02-30 printed a result.\n", "stamps"),
])
def test_each_check_rejects_its_own_hostile_input(repo, text, kind):
    root, _ = repo
    save(root, "docs/plan.md", text)
    code, report = run(repo, commit(root))
    assert code == 1, report
    assert kind in [item["check"] for item in report["findings"]]


def test_reference_definition_edit_rechecks_existing_link(repo):
    root, _ = repo
    save(root, "docs/plan.md", "[Link][destination]\n\n[destination]: <target with space.md>\n")
    base = commit(root)
    save(root, "docs/plan.md", "[Link][destination]\n\n[destination]: missing.md\n")
    code, report = run((root, base), commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "links"


def test_commit_message_closure_requires_exact_intent(repo):
    root, _ = repo
    save(root, "docs/plan.md", "New record.\n")
    head = commit(root, f"fixes {LOCAL_REF}\n\nresolves {FOREIGN_REF}")
    code, report = run(repo, head, "--allow-close", "#7")
    assert code == 1, report
    assert report["findings"][0]["source"] == f"commit:{head}"
    assert "other/repo#7" in report["findings"][0]["detail"]
    code, report = run(repo, head, "--allow-close", "#7", "--allow-close", "other/repo#7")
    assert code == 0, report


@pytest.mark.parametrize("reference", [LOCAL_REF, FOREIGN_REF, "https://github.com/other/repo/issues/7"])
@pytest.mark.parametrize("template", [
    "## Filed, not fixed\n\n- `{reference}` stays open.\n",
    "Closing\n\n1. Tracked work: `{reference}`\n",
    "RESOLVED <!-- intervening markup -->\n\n> {reference}\n",
    "fixes arbitrary intervening prose and punctuation;\n\n{reference}\n",
])
@pytest.mark.parametrize("surface", ["narrative", "commit-message"])
def test_closing_pair_crosses_text_and_markup_with_exact_intent(repo, reference, template, surface):
    root, _ = repo
    text = template.format(reference=reference)
    save(root, "docs/plan.md", text if surface == "narrative" else "New record.\n")
    head = commit(root, text if surface == "commit-message" else "narrative update")
    code, report = run(repo, head)
    assert code == 1, report
    assert report["findings"]
    assert all(item["check"] == "closing-keywords" for item in report["findings"])
    expected_source = "docs/plan.md" if surface == "narrative" else f"commit:{head}"
    assert all(item["source"] == expected_source for item in report["findings"])
    assert all(f"closing reference {reference}:" in item["detail"] for item in report["findings"])
    if reference != LOCAL_REF:
        code, report = run(repo, head, "--allow-close", LOCAL_REF)
        assert code == 1, report
        assert all(f"closing reference {reference}:" in item["detail"] for item in report["findings"])
    code, report = run(repo, head, "--allow-close", reference)
    assert code == 0, report
    assert report["findings"] == []


def test_closing_keywords_pair_with_next_reference_without_reusing_later_references(repo):
    root, _ = repo
    save(root, "docs/plan.md", f"fixes\nresolves\n\n- `{LOCAL_REF}`\n\n{FOREIGN_REF} stays open.\n")
    head = commit(root)
    code, report = run(repo, head)
    assert code == 1, report
    assert [item["line"] for item in report["findings"]] == [1, 2]
    assert all(f"closing reference {LOCAL_REF}:" in item["detail"] for item in report["findings"])
    code, report = run(repo, head, "--allow-close", LOCAL_REF)
    assert code == 0, report


def test_deleting_first_reference_rechecks_new_next_reference(repo):
    root, _ = repo
    save(root, "docs/plan.md", f"fixes\n{LOCAL_REF}\n\n{FOREIGN_REF}\n")
    base = commit(root)
    save(root, "docs/plan.md", f"fixes\n\n{FOREIGN_REF}\n")
    code, report = run((root, base), commit(root), "--allow-close", LOCAL_REF)
    assert code == 1, report
    assert report["findings"][0]["line"] == 1
    assert f"closing reference {FOREIGN_REF}:" in report["findings"][0]["detail"]


@pytest.mark.parametrize("text", [
    f"prefixed fixation resolvedness {LOCAL_REF}\n",
    f"fixes/repo{LOCAL_REF}\n",
    "https://github.com/other/fixes/issues/7\n",
    f"{LOCAL_REF}\n\nfixes a later task without a reference.\n",
])
def test_keyword_substrings_and_reference_identity_do_not_create_closing_pairs(repo, text):
    root, _ = repo
    save(root, "docs/plan.md", text)
    code, report = run(repo, commit(root))
    assert code == 0, report
    assert report["findings"] == []


@pytest.mark.parametrize("text", [
    "[Outside](../../outside.md)\n",
    "[Machine file](/private/tmp/file.md)\n",
    "`make test` at `abcdef0` on 2026-10-10 printed a result.\n",
])
def test_unavailable_inputs_do_not_become_passing_checks(repo, text):
    root, _ = repo
    save(root, "docs/plan.md", text)
    code, report = run(repo, commit(root))
    assert code == 2, report
    assert report["status"] == "unavailable"
    assert report["unavailable"]


def test_multiline_stamp_with_directory_is_observed(repo):
    root, base = repo
    save(root, "docs/plan.md", f"`make test` at `{base}`, in `/project`,\non 2026-10-10 printed a result.\n")
    code, report = run(repo, commit(root))
    assert code == 0, report
    assert report["stamps"][0]["revision"] == base


@pytest.mark.parametrize("delimiter", ["`", "``", "```"])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_wrapped_commonmark_command_rejects_moving_revision(repo, delimiter, newline):
    root, _ = repo
    save(root, "docs/plan.md", f"Observed {delimiter}make{newline}test{delimiter} at "
         f"{delimiter}HEAD{delimiter} on 2026-10-10 printed a result.{newline}")
    code, report = run(repo, commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "stamps"
    assert report["stamps"] == []


@pytest.mark.parametrize("delimiter", ["`", "``", "```"])
def test_wrapped_commonmark_stamp_preserves_historical_identity(repo, delimiter):
    root, base = repo
    save(root, "docs/plan.md", f"Observed {delimiter} make\ntest {delimiter}\nat "
         f"{delimiter} {base} {delimiter},\nin {delimiter}/project\npath{delimiter},\n"
         "on\n2026-10-10 printed a result.\n")
    code, report = run(repo, commit(root))
    assert code == 0, report
    assert report["stamps"] == [{"source": "docs/plan.md", "line": 1,
                                 "command": "make test", "revision": base,
                                 "date": "2026-10-10", "names_head": False}]


@pytest.mark.parametrize("revision,date,expected", [
    ("HE\nAD", "2026-10-10", 1),
    ("abcdef0", "2026-02-30", 1),
    ("abcdef0", "2026-10-10", 2),
])
def test_wrapped_command_does_not_bypass_revision_or_calendar_checks(repo, revision, date, expected):
    root, _ = repo
    save(root, "docs/plan.md", f"``make\ntest`` at ``{revision}`` on {date} printed a result.\n")
    code, report = run(repo, commit(root))
    assert code == expected, report
    assert report["stamps"] == []
    assert (report["findings"] or report["unavailable"])[0]["check"] == "stamps"


@pytest.mark.parametrize("example", [
    "`` `make\ntest` at `HEAD` on 2026-10-10 printed a result. ``\n",
    "    `make\n    test` at `HEAD` on 2026-10-10 printed a result.\n",
    "```markdown\n`make\ntest` at `HEAD` on 2026-10-10 printed a result.\n```\n",
    "\\`make test\\` at \\`HEAD\\` on 2026-10-10 printed a result.\n",
])
def test_stamp_code_examples_are_not_run_claims(repo, example):
    root, _ = repo
    save(root, "docs/plan.md", example)
    code, report = run(repo, commit(root))
    assert code == 0, report
    assert report["stamps"] == []


@pytest.mark.parametrize("extra", [("--root", ""), ("--base", "HEAD"), ("--allow-close", "")])
def test_invalid_cli_inputs_are_explicitly_unavailable(repo, extra):
    root, _ = repo
    save(root, "docs/plan.md", "New record.\n")
    code, report = run(repo, commit(root), *extra)
    assert code == 2, report
    assert report["status"] == "unavailable"
    assert report["error"]
    assert report["unavailable"][0]["detail"] == report["error"]


def test_mixed_changes_supply_no_narrative_preflight_claim(repo):
    root, _ = repo
    save(root, "docs/plan.md", "New record.\n")
    save(root, "code.py", "pass\n")
    code, report = run(repo, commit(root))
    assert code == 0, report
    assert report["status"] == "not-applicable"
    assert report["findings"] == report["unavailable"] == report["stamps"] == []


def test_missing_budgeted_candidate_is_unavailable(repo):
    root, _ = repo
    (root / "docs/plan.md").unlink()
    code, report = run(repo, commit(root))
    assert code == 2, report
    assert "absent" in report["error"]


def test_local_destination_is_literal_not_a_git_pathspec(repo):
    root, _ = repo
    save(root, "docs/plan.md", "[Target](target*.md)\n")
    code, report = run(repo, commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "links"


@pytest.mark.parametrize("separator", ["\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"])
def test_budget_agrees_with_text_stream_lines(repo, separator):
    root, _ = repo
    text = separator.join(["record"] * 21)
    save(root, "docs/plan.md", text)
    # Stream iteration is check_doc_budget's contract; splitlines disagrees.
    with (root / "docs/plan.md").open(encoding="utf-8") as stream:
        assert sum(1 for _ in stream) == 1
    assert len(text.splitlines()) > 20
    code, report = run(repo, commit(root))
    assert code == 0, report
    assert report["status"] == "passed"


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("count,expected", [(20, 0), (21, 1)])
def test_budget_translates_universal_newlines(repo, newline, count, expected):
    root, _ = repo
    save(root, "docs/plan.md", newline.join(["record"] * count))
    code, report = run(repo, commit(root))
    assert code == expected, report
    if expected:
        assert report["findings"][0]["check"] == "budgets"


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("separator", ["\v", "\u2028"])
def test_stamp_block_offsets_ignore_exotic_separators(repo, newline, separator):
    root, _ = repo
    baseline = newline.join(["# Plan", "", f"prefix{separator}suffix", "", "Earlier record.", ""])
    save(root, "docs/plan.md", baseline)
    base = commit(root)
    save(root, "docs/plan.md", baseline.replace("Earlier record.", "`make test` at `HEAD` on 2026-10-10 printed a result."))
    code, report = run((root, base), commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "stamps"
    assert report["findings"][0]["line"] == 5


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_changed_links_follow_commonmark_line_boundaries(repo, newline):
    root, _ = repo
    baseline = newline.join(["# Plan", "", "Earlier record.", "", "Target.", ""])
    save(root, "docs/plan.md", baseline)
    base = commit(root)
    save(root, "docs/plan.md", baseline.replace("Target.", "[Missing](missing.md)"))
    code, report = run((root, base), commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "links"
    assert report["findings"][0]["line"] == 5


def test_exotic_separator_cannot_forge_a_git_hunk(repo):
    root, _ = repo
    baseline = f"Earlier record: resolves {LOCAL_REF}.\n\nRecord.\n"
    save(root, "docs/plan.md", baseline)
    base = commit(root)
    save(root, "docs/plan.md", baseline + "payload\u2028@@ -0,0 +1,1 @@\n")
    code, report = run((root, base), commit(root))
    assert code == 0, report
    assert report["findings"] == []


def test_empty_budget_declaration_is_unavailable(repo):
    root, _ = repo
    config = root / "config/dev-model.yaml"
    text = config.read_text()
    config.write_text(text[:text.index("doc_budgets:")] + "doc_budgets: []\n")
    base = commit(root)
    save(root, "docs/plan.md", "New record.\n")
    code, report = run((root, base), commit(root))
    assert code == 2, report
    assert report["status"] == "unavailable"
    assert "doc_budgets" in report["unavailable"][0]["detail"]


@pytest.mark.parametrize("text,kind", [("[Missing](missing.md)\n", "links"), ("`make test` at `HEAD` on 2026-10-10 printed a result.\n", "stamps")])
def test_git_color_settings_do_not_change_hunk_coordinates(repo, text, kind):
    root, _ = repo
    git(root, "config", "color.ui", "always")
    git(root, "config", "color.diff", "always")
    save(root, "docs/plan.md", text)
    code, report = run(repo, commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == kind


@pytest.mark.parametrize("before,after,kind", [
    ("```\nprefix\n\n[Missing](missing.md)\n```\n",
     "prefix\n\n[Missing](missing.md)\n```\n", "links"),
    ("```\nprefix\n\n`make test` at `HEAD` on 2026-10-10 printed a result.\n```\n",
     "prefix\n\n`make test` at `HEAD` on 2026-10-10 printed a result.\n```\n", "stamps"),
    (f"fixes\nintervening text\n{LOCAL_REF}\n", f"fixes\n{LOCAL_REF}\n", "closing-keywords"),
    (f"fixes\n\nintervening text\n\n{LOCAL_REF}\n", f"fixes\n\n{LOCAL_REF}\n", "closing-keywords"),
    ("[Link][destination]\n\n[destination]: <target with space.md>\n[destination]: missing.md\n",
     "[Link][destination]\n\n[destination]: missing.md\n", "links"),
])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_deletions_recheck_affected_meaning(repo, before, after, kind, newline):
    root, _ = repo
    save(root, "docs/plan.md", before.replace("\n", newline))
    base = commit(root)
    save(root, "docs/plan.md", after.replace("\n", newline))
    code, report = run((root, base), commit(root))
    assert code == 1, report
    assert kind in [item["check"] for item in report["findings"]]


def test_deletions_preserve_untouched_record_scope(repo):
    root, _ = repo
    untouched = (f"Earlier record: resolves {LOCAL_REF}. [Missing](missing.md)\n"
                 "`make test` at `HEAD` on 2026-10-10 printed a result.\n\n")
    save(root, "docs/plan.md", untouched + "Separate record.\n\nRemoved tail.\n")
    base = commit(root)
    save(root, "docs/plan.md", untouched + "Separate record.\n")
    code, report = run((root, base), commit(root))
    assert code == 0, report
    assert report["findings"] == []


def test_deletions_preserve_existing_closing_matches(repo):
    root, _ = repo
    baseline = f"Earlier record: resolves {LOCAL_REF}.\n\nRemoved tail.\n"
    save(root, "docs/plan.md", baseline)
    base = commit(root)
    save(root, "docs/plan.md", baseline[:baseline.index("\n\n")] + "\n")
    code, report = run((root, base), commit(root))
    assert code == 0, report
    assert report["findings"] == []


def test_deletions_detect_duplicate_new_closing_matches(repo):
    root, _ = repo
    baseline = f"resolves\n{LOCAL_REF}\n\nresolves\nintervening text\n{LOCAL_REF}\n"
    save(root, "docs/plan.md", baseline)
    base = commit(root)
    save(root, "docs/plan.md", baseline.replace("intervening text\n", ""))
    code, report = run((root, base), commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "closing-keywords"
    assert report["findings"][0]["line"] == 4


@pytest.mark.parametrize("before,after,kind", [
    (f"resolves\n{LOCAL_REF}\n\nKeep boundary.\n\nresolves\nintervening text\n{LOCAL_REF}\n",
     f"Keep boundary.\n\nresolves\n{LOCAL_REF}\n", "closing-keywords"),
    ("[Missing](missing.md)\n\n```\nprefix\n\n[Missing](missing.md)\n```\n",
     "prefix\n\n[Missing](missing.md)\n```\n", "links"),
])
def test_removed_old_match_cannot_mask_new_deletion_effect(repo, before, after, kind):
    root, _ = repo
    save(root, "docs/plan.md", before)
    base = commit(root)
    save(root, "docs/plan.md", after)
    code, report = run((root, base), commit(root))
    assert code == 1, report
    assert kind in [item["check"] for item in report["findings"]]


def test_deleted_reference_definition_rechecks_document_links(repo):
    root, _ = repo
    save(root, "docs/plan.md", "[Missing](missing.md)\n\n[unused]: <target with space.md>\n")
    base = commit(root)
    save(root, "docs/plan.md", "[Missing](missing.md)\n")
    code, report = run((root, base), commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "links"


def test_new_narrative_file_has_no_prior_blocks(repo):
    root, _ = repo
    save(root, "docs/archive.md", "[Missing](missing.md)\n")
    code, report = run(repo, commit(root))
    assert code == 1, report
    assert report["findings"][0]["source"] == "docs/archive.md"


def test_utf8_document_with_nul_has_textual_change_coordinates(repo):
    root, _ = repo
    save(root, "docs/plan.md", "Record\0\n\n[Missing](missing.md)\n")
    code, report = run(repo, commit(root))
    assert code == 1, report
    assert report["findings"][0]["check"] == "links"


@pytest.mark.parametrize("status", ["passed", "not-applicable", "unavailable"])
def test_cli_does_not_write_fresh_engine_or_input_tree(repo, tmp_path, status):
    require_kit_paths("scripts/check_record_prose.py", "scripts/lib/kitconfig.py")
    root, _ = repo
    fresh = tmp_path / "fresh-engine"
    (fresh / "lib").mkdir(parents=True)
    shutil.copyfile(ENGINE, fresh / ENGINE.name)
    shutil.copyfile(ENGINE.parent / "lib/kitconfig.py", fresh / "lib/kitconfig.py")
    save(root, ".gitignore", "__pycache__/\n*.pyc\n")
    base = commit(root)
    save(root, "docs/plan.md", "New record.\n")
    if status == "not-applicable":
        save(root, "code.py", "pass\n")
    head = commit(root)

    def snapshot(path):
        return {p.relative_to(path).as_posix(): p.read_bytes()
                for p in path.rglob("*") if p.is_file()}

    before = snapshot(fresh), snapshot(root)
    env = os.environ.copy()
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    env.pop("PYTHONPYCACHEPREFIX", None)
    result = subprocess.run(
        ["uv", "run", str(fresh / ENGINE.name), "--root", str(root),
         "--base", "HEAD" if status == "unavailable" else base, "--head", head, "--json"],
        cwd=root, env=env, capture_output=True, text=True, timeout=90,
    )
    assert result.stdout, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == status
    assert result.returncode == (2 if status == "unavailable" else 0)
    assert (snapshot(fresh), snapshot(root)) == before
