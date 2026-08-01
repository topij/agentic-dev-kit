"""What pins the panel-prompt assembler — and what it deliberately cannot promise.

`panel_prompt.py` exists because launch prompts were hand-authored per lens per
round (#214), so an omitted contract item was invisible and asserted-but-wrong
provenance sent lenses looking for things that were not there.

The properties worth pinning are the ones a future edit could quietly break while
the script still emits something plausible-looking:

- the contract is **quoted from the doctrine**, not restated here — so changing
  the doctrine changes the prompt, and no second copy can drift;
- it **refuses** rather than emitting a prompt that would mislead a lens (empty
  diff, unknown lens, unparseable contract);
- the base-provenance label **matches the path actually taken** — the one claim
  this script makes about itself, and the one that would be false on exactly one
  code path if nobody pinned it.

**What these tests do NOT cover**, stated because a shorter list would overstate
them: they do not run `git ls-remote`, so the remote-resolution path is exercised
only through an injected base; they say nothing about whether a lens *obeys* the
assembled prompt; and they do not check the doctrine's prose, which is the same
gap `test_mutation_gate.py` records for itself.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

REPO_ROOT = find_repo_root(Path(__file__).resolve())
ENGINE = engine_dir(Path(__file__).resolve()) / "panel_prompt.py"
DOCTRINE = REPO_ROOT / "docs" / "agentic-dev-kit" / "fallback-review-panel.md"


def _load():
    sys.path.insert(0, str(ENGINE.parent))
    import panel_prompt

    return panel_prompt


def _two_commits() -> tuple[str, str]:
    """A real base/head pair with a non-empty diff between them."""
    log = subprocess.run(
        ["git", "log", "--format=%H", "-40"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return log[-1], log[0]


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


# --- the contract is quoted, never restated -------------------------------------


def test_every_contract_item_in_the_doctrine_reaches_the_prompt():
    """The #214 defect in one assertion: an omitted item must be impossible."""
    pp = _load()
    section, names = pp.contract(DOCTRINE)
    assert names, "doctrine parsed to zero contract items"

    base, head = _two_commits()
    out = _run("--lens", "adversarial", "--head", head, "--base", base)
    assert out.returncode == 0, out.stderr
    for name in names:
        assert name in out.stdout, f"contract item {name!r} never reached the prompt"
    assert section in out.stdout, "contract section was not quoted verbatim"


def test_the_contract_is_read_from_the_doctrine_not_embedded_in_the_script(tmp_path):
    """Mutate the doctrine; the parsed contract must move with it.

    This is the anti-drift property. If someone inlines the contract into the
    script for speed, this fails — which is the point.
    """
    pp = _load()
    doctored = tmp_path / "doctrine.md"
    text = DOCTRINE.read_text().replace(
        "1. **Fresh context.**", "1. **Wholly invented item.**", 1
    )
    doctored.write_text(text)

    _, names = pp.contract(doctored)
    assert "Wholly invented item" in names
    assert "Fresh context" not in names


def test_a_doctrine_with_no_contract_items_is_refused(tmp_path):
    pp = _load()
    doctored = tmp_path / "doctrine.md"
    doctored.write_text("# Doc\n\n## The contract every lens gets\n\nProse, no list.\n\n## Next\n")
    with pytest.raises(pp.PromptError, match="0 contract items"):
        pp.contract(doctored)


def test_a_renamed_contract_heading_is_refused_rather_than_guessed(tmp_path):
    pp = _load()
    doctored = tmp_path / "doctrine.md"
    doctored.write_text("# Doc\n\n## Some other heading\n\n1. **A.** b\n")
    with pytest.raises(pp.PromptError, match="no '## The contract"):
        pp.contract(doctored)


def test_sub_bullets_are_not_counted_as_contract_items(tmp_path):
    """Item 5 and item 10 carry indented numbered sub-lists in the real doctrine.

    Anchoring to column 0 is what keeps the count honest; a mutation to `re.MULTILINE`
    anchoring would inflate it silently.
    """
    pp = _load()
    doctored = tmp_path / "doctrine.md"
    doctored.write_text(
        "## The contract every lens gets\n\n"
        "1. **Real one.** body\n"
        "   1. **Nested decoy.** body\n"
        "2. **Real two.** body\n"
    )
    _, names = pp.contract(doctored)
    assert names == ["Real one", "Real two"]


# --- it refuses rather than misleading a lens -----------------------------------


def test_an_empty_diff_is_refused():
    """A lens handed an empty diff reports a clean pass over nothing."""
    _, head = _two_commits()
    out = _run("--lens", "adversarial", "--head", head, "--base", head)
    assert out.returncode == 2
    assert "empty" in out.stderr


def test_a_lens_outside_the_configured_roster_is_refused():
    base, head = _two_commits()
    out = _run("--lens", "minted-for-the-occasion", "--head", head, "--base", base)
    assert out.returncode == 2
    assert "not in review.fallback_panel.lenses" in out.stderr


def test_a_head_that_is_not_a_commit_is_refused():
    base, _ = _two_commits()
    out = _run("--lens", "adversarial", "--head", "deadbeefdeadbeef", "--base", base)
    assert out.returncode == 2


# --- the script's one claim about itself ----------------------------------------


def test_base_provenance_label_matches_the_path_actually_taken():
    """An author-supplied base must never be described as remote-resolved.

    This is the only self-referential claim the prompt makes, and it is false on
    exactly one code path if the label is hardcoded. Pinning both directions.
    """
    pp = _load()
    base, head = _two_commits()

    supplied = _run("--lens", "adversarial", "--head", head, "--base", base)
    assert supplied.returncode == 0, supplied.stderr
    assert "NOT resolved from the remote" in supplied.stdout
    assert "not supplied by the author" not in supplied.stdout

    remote_wording = pp.render(
        lens="adversarial",
        focus="f",
        head=head,
        base=base,
        diffstat="1 file changed",
        contract_text="1. **X.** y",
        item_names=["X"],
        repo_slug="o/r",
        branch="b",
        compute={},
        scratch=None,
        pr=None,
        carry_forward=None,
        verify_command=None,
        base_from_remote=True,
    )
    assert "not supplied by the author" in remote_wording
    assert "NOT resolved from the remote" not in remote_wording


def test_the_same_inputs_produce_the_same_prompt():
    """Round-to-round framing differences must be deliberate, not variance."""
    base, head = _two_commits()
    a = _run("--lens", "adversarial", "--head", head, "--base", base)
    b = _run("--lens", "adversarial", "--head", head, "--base", base)
    assert a.returncode == 0 and b.returncode == 0
    assert a.stdout == b.stdout


def test_carry_forward_reaches_the_prompt_when_given_and_is_absent_otherwise():
    """The lever measured on #218: what prior rounds covered, carried into the aim."""
    base, head = _two_commits()
    marker = "Rounds 1-3 found everything in the claims and nothing in the content."

    with_it = _run("--lens", "adversarial", "--head", head, "--base", base, "--carry-forward", marker)
    assert marker in with_it.stdout
    assert "What prior rounds have and have not covered" in with_it.stdout

    without = _run("--lens", "adversarial", "--head", head, "--base", base)
    assert "What prior rounds have and have not covered" not in without.stdout


def test_the_verification_command_is_never_guessed():
    """No config key holds it, so an unset command must be omitted, not invented."""
    base, head = _two_commits()
    out = _run("--lens", "adversarial", "--head", head, "--base", base)
    assert "verification command" not in out.stdout

    named = _run(
        "--lens", "adversarial", "--head", head, "--base", base, "--verify-command", "make test"
    )
    assert "`make test` is this repo's verification command" in named.stdout
