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
DOCTRINE = Path("docs") / "agentic-dev-kit" / "fallback-review-panel.md"
DOCTRINE_TEXT = (REPO_ROOT / DOCTRINE).read_text()


def _load():
    sys.path.insert(0, str(ENGINE.parent))
    import panel_prompt

    return panel_prompt


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A fixture repo with two commits, the real doctrine, and a lens roster.

    Deliberately NOT this repo. An earlier version of these tests read
    ``git log`` here for a base/head pair, which works locally and returns a
    single commit under CI's shallow checkout — base == head, and the engine
    correctly refused the empty diff. The tests were the defect, not the engine,
    and depending on ambient history is the thing that made them one.
    """
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / "docs" / "agentic-dev-kit").mkdir(parents=True)

    # The real doctrine, so the contract these tests assert on is the shipped one.
    (root / DOCTRINE).write_text(DOCTRINE_TEXT)
    (root / "config" / "dev-model.yaml").write_text(
        "vcs:\n  protected_branch: main\n"
        "review:\n"
        "  fallback_panel:\n"
        "    lenses:\n"
        "      - name: adversarial\n"
        "        focus: prove it wrong\n"
        "      - name: correctness\n"
        "        focus: ask what it says\n"
        "    lens_compute:\n"
        "      claude:\n"
        "        model: sonnet\n"
        "        effort: high\n"
    )

    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "remote.origin.url", "https://github.com/o/r.git")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")

    (root / "a.txt").write_text("head\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "head")
    return root


def _revs(root: Path) -> tuple[str, str]:
    return _git(root, "rev-parse", "HEAD~1"), _git(root, "rev-parse", "HEAD")


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE), "--root", str(root), *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


# --- the contract is quoted, never restated -------------------------------------


def test_every_contract_item_in_the_doctrine_reaches_the_prompt(repo):
    """The #214 defect in one assertion: an omitted item must be impossible."""
    pp = _load()
    section, names = pp.contract(repo / DOCTRINE)
    assert names, "doctrine parsed to zero contract items"

    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
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
    text = DOCTRINE_TEXT.replace(
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


def test_an_empty_diff_is_refused(repo):
    """A lens handed an empty diff reports a clean pass over nothing."""
    _, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", head)
    assert out.returncode == 2
    assert "empty" in out.stderr


def test_a_lens_outside_the_configured_roster_is_refused(repo):
    base, head = _revs(repo)
    out = _run(repo, "--lens", "minted-for-the-occasion", "--head", head, "--base", base)
    assert out.returncode == 2
    assert "not in review.fallback_panel.lenses" in out.stderr


def test_a_head_that_is_not_a_commit_is_refused(repo):
    base, _ = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", "deadbeefdeadbeef", "--base", base)
    assert out.returncode == 2


# --- the script's one claim about itself ----------------------------------------


def test_base_provenance_label_matches_the_path_actually_taken(repo):
    """An author-supplied base must never be described as remote-resolved.

    This is the only self-referential claim the prompt makes, and it is false on
    exactly one code path if the label is hardcoded. Pinning both directions.
    """
    pp = _load()
    base, head = _revs(repo)

    supplied = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
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


def test_the_same_inputs_produce_the_same_prompt(repo):
    """Round-to-round framing differences must be deliberate, not variance."""
    base, head = _revs(repo)
    a = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
    b = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
    assert a.returncode == 0 and b.returncode == 0
    assert a.stdout == b.stdout


def test_carry_forward_reaches_the_prompt_when_given_and_is_absent_otherwise(repo):
    """The lever measured on #218: what prior rounds covered, carried into the aim."""
    base, head = _revs(repo)
    marker = "Rounds 1-3 found everything in the claims and nothing in the content."

    with_it = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--carry-forward", marker)
    assert marker in with_it.stdout
    assert "What prior rounds have and have not covered" in with_it.stdout

    without = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
    assert "What prior rounds have and have not covered" not in without.stdout


def test_the_verification_command_is_never_guessed(repo):
    """No config key holds it, so an unset command must be omitted, not invented."""
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
    assert "verification command" not in out.stdout

    named = _run(
        repo, "--lens", "adversarial", "--head", head, "--base", base, "--verify-command", "make test"
    )
    assert "`make test` is this repo's verification command" in named.stdout


def test_a_level_three_heading_is_not_mistaken_for_the_contract(tmp_path):
    """`### The contract...` contains `## The contract...` as a substring.

    A plain `str.find` matches it at offset 1 and would emit a subsection as the
    contract. Found by CodeRabbit on the PR that added this engine.
    """
    pp = _load()
    doctored = tmp_path / "doctrine.md"
    doctored.write_text(
        "# Doc\n\n### The contract every lens gets\n\n1. **Decoy.** not the real one\n"
    )
    with pytest.raises(pp.PromptError, match="no '## The contract"):
        pp.contract(doctored)


def test_the_phrase_quoted_in_prose_is_not_mistaken_for_the_heading(tmp_path):
    pp = _load()
    doctored = tmp_path / "doctrine.md"
    doctored.write_text(
        "# Doc\n\nSee the ## The contract every lens gets section below.\n\n"
        "1. **Decoy.** not the real one\n"
    )
    with pytest.raises(pp.PromptError, match="no '## The contract"):
        pp.contract(doctored)


def test_a_level_three_subheading_does_not_truncate_the_contract(tmp_path):
    """Bounding on `\\n## ` must not stop at a `###` sub-heading inside the section."""
    pp = _load()
    doctored = tmp_path / "doctrine.md"
    doctored.write_text(
        "## The contract every lens gets\n\n"
        "1. **First.** body\n\n"
        "### A subsection inside the contract\n\n"
        "2. **Second.** body\n\n"
        "## Running it\n\n"
        "3. **Not a contract item.** body\n"
    )
    _, names = pp.contract(doctored)
    assert names == ["First", "Second"]
