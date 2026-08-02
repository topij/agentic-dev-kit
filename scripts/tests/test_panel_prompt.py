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
from conftest import require_kit_paths

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_layout import engine_dir, find_repo_root  # noqa: E402

REPO_ROOT = find_repo_root(Path(__file__).resolve())
ENGINE = engine_dir(Path(__file__).resolve()) / "panel_prompt.py"
DOCTRINE = Path("docs") / "agentic-dev-kit" / "fallback-review-panel.md"

# NOT a module-level marker. An earlier version marked the whole module on the
# doctrine, reasoning that `panel_prompt.py` is non-functional without it. That
# over-reached: 15 test cases here never read the shipped file — they parse
# synthetic doctrines they write themselves, or exercise `_repo_slug()`, a pure
# string function with three prior lens-found bugs. Marking the module skipped
# all of them in exactly the tree #226 says `/adopt` produces, losing coverage
# of shipped parsing logic that such a tree still has. Both lenses, PR #232
# round 1.
#
# The dependency is instead declared where it actually arises — in
# `doctrine_text()`, which the `repo` fixture and one test call — so a new test
# inherits it by using the fixture rather than by remembering a decorator.


def test_the_declared_path_matches_the_doctrine_path():
    """`doctrine_text()` names the path as a string LITERAL so
    `test_kit_repo_only.py` can find it by scanning the source; `DOCTRINE` is a
    `Path` built separately. Two spellings of one path drift, so this pins them
    — without it a doctrine rename would leave the requirement naming a file
    that no longer exists, and skip every test using it, silently."""
    assert str(DOCTRINE) == "docs/agentic-dev-kit/fallback-review-panel.md"


def doctrine_text() -> str:
    """The shipped doctrine, read at CALL time rather than import time.

    This was a module-level `read_text()`, which raised during **collection** in
    any tree without the doctrine — so pytest aborted and ran **zero** tests,
    rather than failing the handful that need the file. `/adopt` Step 3 does not
    name `fallback-review-panel.md` among the docs it installs, so that was not
    the extreme floor: it was a by-the-book adoption (#226).

    A function and not a fixture, deliberately: one caller wants it inside a
    test body and one inside another fixture, and a fixture would thread a
    parameter through call sites that need nothing else.
    """
    require_kit_paths("docs/agentic-dev-kit/fallback-review-panel.md")
    return (REPO_ROOT / DOCTRINE).read_text(encoding="utf-8")


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
    (root / DOCTRINE).write_text(doctrine_text())
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


def _run_ok(root: Path, *args: str) -> bool:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=False).returncode == 0


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
    text = doctrine_text().replace(
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
    """Asserting only `returncode == 2` pinned nothing: with `_require_commit`'s body
    replaced by a passthrough, the refusal still arrived — from the branch-tip check,
    for an unrelated reason. The message is what discriminates."""
    base, _ = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", "deadbeefdeadbeef", "--base", base)
    assert out.returncode == 2
    assert "is not a commit in this repo" in out.stderr


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


# --- findings from the adversarial lens on PR #219 -------------------------------


def test_a_detached_checkout_is_refused_rather_than_named_HEAD(repo):
    """`rev-parse --abbrev-ref HEAD` returns the literal 'HEAD' when detached.

    That is the state of every worktree built at a pinned sha for review, and of a
    default CI PR checkout. Rendering it produced `**Branch:** HEAD` at exit 0 — a
    plausible-looking lie in the field the contract requires. Found by mutation:
    hardwiring the branch to a constant passed the entire suite.
    """
    base, head = _revs(repo)
    _git(repo, "checkout", "-q", "--detach", head)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
    assert out.returncode == 2
    assert "detached" in out.stderr
    assert "**Branch:** HEAD" not in out.stdout


def test_an_explicit_branch_is_accepted_on_a_detached_checkout(repo):
    """The refusal must be escapable the documented way, or it just blocks review."""
    base, head = _revs(repo)
    _git(repo, "checkout", "-q", "--detach", head)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--branch", "topic/x")
    assert out.returncode == 0, out.stderr
    assert "- **Branch:** topic/x" in out.stdout


def test_the_branch_under_review_is_actually_rendered(repo):
    """No test asserted on the Branch line at all; hardwiring it killed nothing."""
    base, head = _revs(repo)
    _git(repo, "checkout", "-q", "-b", "feat/observed")
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
    assert out.returncode == 0, out.stderr
    assert "- **Branch:** feat/observed" in out.stdout


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/topij/agentic-dev-kit.git", "topij/agentic-dev-kit"),
        ("git@github.com:topij/agentic-dev-kit.git", "topij/agentic-dev-kit"),
        ("https://gitlab.com/group/subgroup/proj.git", "group/subgroup/proj"),
        ("git@gitlab.com:group/subgroup/proj.git", "group/subgroup/proj"),
        ("https://host/a/b/c/d", "a/b/c/d"),
    ],
)
def test_nested_remote_paths_are_not_truncated(url, expected):
    """Taking only the last two segments renders a wrong-but-plausible repo for
    forges with nested namespaces — GitLab subgroups, Bitbucket projects."""
    pp = _load()
    assert pp._repo_slug(url) == expected


def test_the_no_worktree_write_safety_instruction_is_present(repo):
    """Unpinned, this inverted cleanly under mutation while 641 tests passed.

    Item 7/#136 is the reason it matters: one lens nearly destroyed live work.
    """
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--branch", "b")
    assert "do not write into any tree you were handed" in out.stdout
    assert "No worktree was provided" in out.stdout


def test_a_provided_worktree_is_named_and_the_no_worktree_warning_is_dropped(repo):
    base, head = _revs(repo)
    out = _run(
        repo, "--lens", "adversarial", "--head", head, "--base", base,
        "--branch", "b", "--scratch", "/abs/scratch/lens-x",
    )
    assert "/abs/scratch/lens-x" in out.stdout
    assert "No worktree was provided" not in out.stdout


def test_a_renumbering_slip_is_refused_even_though_the_count_is_unchanged(tmp_path):
    """A renumbering slip changes no count: `len(names)` is the same either way."""
    pp = _load()
    doctored = tmp_path / "doctrine.md"
    doctored.write_text(
        "## The contract every lens gets\n\n"
        "1. **First.** body\n"
        "3. **Third, skipping two.** body\n"
    )
    with pytest.raises(pp.PromptError, match="not 1..2"):
        pp.contract(doctored)


# --- round 2 findings: the branch fix did not close its class -------------------


def test_a_worktree_on_its_own_lane_branch_is_refused(repo, tmp_path):
    """`dev_session.sh` builds lanes with `git worktree add -b`, so a review tree
    can sit on a real branch that is NOT the branch under review.

    The first fix refused only the literal 'HEAD'. This case renders a real-looking
    branch name instead — strictly worse, because 'HEAD' at least reads as a
    placeholder. The checkable property is that an auto-detected branch is the
    branch under review only if its tip IS the head under review.
    """
    base, head = _revs(repo)
    lane = tmp_path / "lane"
    _git(repo, "worktree", "add", "-b", "lane/throwaway", str(lane), base)
    out = _run(lane, "--lens", "adversarial", "--head", head, "--base", base)
    assert out.returncode == 2, out.stdout
    assert "is not the one under review" in out.stderr
    assert "lane/throwaway" not in out.stdout


def test_a_branch_whose_tip_is_the_head_is_accepted(repo):
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
    assert out.returncode == 0, out.stderr
    assert "- **Branch:** main" in out.stdout


def test_an_empty_branch_override_is_refused_not_silently_ignored(repo):
    """`if override:` let `--branch ''` fall through to auto-detection."""
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--branch", "")
    assert out.returncode == 2
    assert "empty" in out.stderr


# --- round 2 findings: resolve_base had zero coverage ---------------------------


def test_a_base_branch_matching_several_refs_is_refused(repo, tmp_path):
    """`git ls-remote` takes a PATTERN. A glob matched several refs and the first
    was chosen silently — defeating the one property the docstring names as this
    script's reason for existing.
    """
    pp = _load()
    upstream = tmp_path / "upstream"
    _git(repo, "clone", "-q", "--bare", str(repo), str(upstream))
    _git(repo, "branch", "main-extra")
    _git(repo, "remote", "set-url", "origin", str(upstream))
    _git(repo, "push", "-q", "origin", "main-extra")

    with pytest.raises(pp.PromptError, match="matched 2 refs"):
        pp.resolve_base(repo, "main*")


def test_a_base_branch_matching_exactly_one_ref_resolves(repo, tmp_path):
    pp = _load()
    upstream = tmp_path / "upstream2"
    _git(repo, "clone", "-q", "--bare", str(repo), str(upstream))
    _git(repo, "remote", "set-url", "origin", str(upstream))
    assert pp.resolve_base(repo, "main") == _git(repo, "rev-parse", "HEAD")


def test_a_base_branch_matching_no_ref_is_refused(repo, tmp_path):
    pp = _load()
    upstream = tmp_path / "upstream3"
    _git(repo, "clone", "-q", "--bare", str(repo), str(upstream))
    _git(repo, "remote", "set-url", "origin", str(upstream))
    with pytest.raises(pp.PromptError, match="has no refs/heads/"):
        pp.resolve_base(repo, "no-such-branch")


def test_a_remote_url_with_no_repo_path_does_not_render_the_host_as_the_repo():
    pp = _load()
    assert pp._repo_slug("https://github.com") == "https://github.com"
    assert pp._repo_slug("https://github.com/o/r") == "o/r"


def test_the_branch_escape_hatch_refuses_the_value_it_exists_to_refuse(repo):
    """`--branch HEAD` passed straight through and rendered the identical lie the
    ambient path refuses. git forbids a branch named HEAD, so nothing valid is lost.
    """
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--branch", "HEAD")
    assert out.returncode == 2
    assert "**Branch:** HEAD" not in out.stdout


def test_an_empty_base_override_is_refused_not_silently_remote_resolved(repo):
    """`base_from_remote` used `is None` while the value used `or`, so `--base ""`
    resolved from the remote while the prompt said the author supplied it."""
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", "", "--branch", "b")
    assert out.returncode == 2
    assert "empty" in out.stderr


# --- round 3: the class, not three more instances -------------------------------


@pytest.mark.parametrize(
    "flag", ["--branch", "--base", "--base-branch", "--scratch", "--carry-forward", "--verify-command"]
)
def test_every_optional_override_refuses_an_empty_value(repo, flag):
    """Three rounds each found this in a DIFFERENT flag, because each was fixed as
    an instance. `--base-branch ""` silently fell back to the config default while
    the prompt still said the base was resolved from the remote.
    """
    base, head = _revs(repo)
    args = ["--lens", "adversarial", "--head", head, "--base", base, "--branch", "b"]
    # Replace the flag under test with an empty value (appending is fine for the
    # ones not already present).
    if flag in args:
        args[args.index(flag) + 1] = ""
    else:
        args += [flag, ""]
    out = _run(repo, *args)
    assert out.returncode == 2, f"{flag} with an empty value was accepted: {out.stdout[:200]}"
    assert flag in out.stderr


def test_a_local_path_remote_is_not_rendered_as_an_org_repo_slug():
    """`file:///Users/topi/Coding/kit.git` split to `Users/topi/Coding/kit`, which
    reads exactly like a real org/repo. This kit's own tests set a local origin."""
    pp = _load()
    for url in (
        "file:///Users/topi/Coding/agentic-dev-kit.git",
        "/Users/topi/Coding/local-clone.git",
        "./relative-clone",
    ):
        assert pp._repo_slug(url) == url, f"{url} rendered as a plausible org/repo"
    assert pp._repo_slug("https://github.com/o/r.git") == "o/r"


def test_an_overridden_branch_is_marked_as_asserted_not_verified(repo):
    """Every neighbouring fact in the prompt is git-verified. An overridden branch
    is not, and rendering it unqualified gave an assertion a measurement's weight.
    `--base`'s override already carried such a caveat; `--branch`'s did not."""
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--branch", "asserted/x")
    assert out.returncode == 0, out.stderr
    assert "not verified against this checkout" in out.stdout

    ambient = _run(repo, "--lens", "adversarial", "--head", head, "--base", base)
    assert ambient.returncode == 0, ambient.stderr
    assert "not verified against this checkout" not in ambient.stdout


def test_an_abbreviated_head_is_normalised_to_the_full_sha(repo):
    """`_require_commit`'s real job is normalisation, not just refusal.

    Unpinned, a future edit could render a moving branch name where the prompt
    promises a pinned sha — which **Right revision** calls reason enough on its own.
    """
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head[:8], "--base", base, "--branch", "b")
    assert out.returncode == 0, out.stderr
    assert f"`{head}`" in out.stdout, "abbreviated head was not expanded to the full sha"
    assert f"`{head[:8]}`" not in out.stdout


def test_a_branch_name_passed_as_head_is_normalised_to_a_sha(repo):
    """A branch moves; a sha does not. The prompt must never carry the name."""
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", "main", "--base", base, "--branch", "b")
    assert out.returncode == 0, out.stderr
    assert f"`{head}`" in out.stdout
    assert "**Head sha under review:** `main`" not in out.stdout


# --- round 4: guards that refused a legitimate invocation ------------------------


def test_a_shallow_clone_gets_an_actionable_error_not_a_staleness_one(repo, tmp_path):
    """`ls-remote` transfers no objects, so a `--depth 1` clone has the feature
    branch's history but not the base's. Validating the base locally then failed on
    a base that is provably CURRENT, with a message reading like staleness and
    naming no remedy — the engine refusing an entirely legitimate invocation.
    """
    pp = _load()
    upstream = tmp_path / "up"
    _git(repo, "clone", "-q", "--bare", str(repo), str(upstream))
    _git(repo, "checkout", "-q", "-b", "feature")
    (repo / "f.txt").write_text("f\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "feature work")
    _git(repo, "remote", "set-url", "origin", str(upstream))
    _git(repo, "push", "-q", "origin", "feature")

    shallow = tmp_path / "shallow"
    # `file://` is required: git treats a plain local path as a hardlink clone and
    # silently ignores --depth, so the fixture would not be shallow at all.
    _git(repo, "clone", "-q", "--depth", "1", "--branch", "feature",
         f"file://{upstream}", str(shallow))
    base = _git(repo, "rev-parse", "main")
    assert not _run_ok(shallow, "cat-file", "-e", base), "fixture did not produce a shallow clone"

    with pytest.raises(pp.PromptError) as exc:
        pp._require_base_object(shallow, base, "main", True)
    msg = str(exc.value)
    assert "not in this clone" in msg
    assert "git fetch origin main" in msg, "the error must name the remedy"
    assert "the sha is\ncurrent" in msg or "current" in msg


def test_a_base_object_that_is_present_still_resolves(repo):
    pp = _load()
    base, head = _revs(repo)
    assert pp._require_base_object(repo, base, "main", True) == base


def test_an_empty_runtime_is_refused_like_every_other_override(repo):
    """`--runtime` was left out of the sweep while `_override`'s docstring claimed
    'every optional flag'."""
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--branch", "b",
               "--runtime", "")
    assert out.returncode == 2
    assert "--runtime" in out.stderr


def test_a_runtime_with_no_configured_compute_says_so_rather_than_omitting_it(repo):
    """An unconfigured runtime legitimately means 'inherit', but a TYPO looked
    identical — both silently dropped the line."""
    base, head = _revs(repo)
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--branch", "b",
               "--runtime", "clade")
    assert out.returncode == 0, out.stderr
    assert "No compute configured for runtime 'clade'" in out.stdout

    configured = _run(repo, "--lens", "adversarial", "--head", head, "--base", base, "--branch", "b")
    assert "Run at:" in configured.stdout


# --- round 5: the flag outside the sweep, and an unearned certainty --------------


def test_an_empty_root_is_refused_and_does_not_silently_retarget_the_cwd(repo, tmp_path):
    """`--root` was the one optional flag outside the `_override` sweep, and
    argparse's `type=Path` hid it: `Path("")` is `PosixPath(".")`, which is TRUTHY,
    so `args.root or REPO_ROOT` never fell through. `--root ""` silently reviewed
    whatever repo the process happened to be standing in.
    """
    base, head = _revs(repo)
    out = subprocess.run(
        [sys.executable, str(ENGINE), "--root", "", "--lens", "adversarial",
         "--head", head, "--base", base, "--branch", "b"],
        cwd=repo, capture_output=True, text=True, check=False,
    )
    assert out.returncode == 2, out.stdout[:300]
    assert "--root" in out.stderr


def test_an_omitted_root_still_defaults_to_the_engines_own_repo(repo):
    """The fallback the empty-string bug disabled must still work."""
    out = subprocess.run(
        [sys.executable, str(ENGINE), "--lens", "adversarial", "--head", "HEAD", "--branch", "b"],
        cwd=repo, capture_output=True, text=True, check=False,
    )
    # Resolves against the ENGINE's repo, not `repo` — so it must not see repo's shas.
    assert "o/r" not in out.stdout


@pytest.mark.parametrize("flag", ["--head", "--lens"])
def test_required_flags_reject_an_empty_value(repo, flag):
    """argparse guarantees presence, not content; an empty --head reached git as a
    blank revision and produced a message with a hole in it."""
    base, head = _revs(repo)
    args = ["--lens", "adversarial", "--head", head, "--base", base, "--branch", "b"]
    args[args.index(flag) + 1] = ""
    out = _run(repo, *args)
    assert out.returncode == 2
    assert flag in out.stderr


def test_an_author_supplied_base_is_not_told_the_sha_is_current(repo):
    """Round 4's message asserted "the sha is current" on BOTH paths. On the
    --base path nothing verified that, so a fat-fingered sha was confidently told
    to run a fetch that cannot help. The render already calls an author-supplied
    base unverified; the refusal must agree with it.
    """
    _, head = _revs(repo)
    bogus = "deadbeef" * 5
    out = _run(repo, "--lens", "adversarial", "--head", head, "--base", bogus, "--branch", "b")
    assert out.returncode == 2
    assert "the sha is current" not in out.stderr
    assert "nothing here has verified which" in out.stderr


def test_a_remote_resolved_base_still_says_the_sha_is_current(repo, tmp_path):
    """The earned half of that distinction must survive."""
    pp = _load()
    with pytest.raises(pp.PromptError) as exc:
        pp._require_base_object(repo, "deadbeef" * 5, "main", True)
    assert "the sha is current" in str(exc.value)


def test_an_object_that_exists_but_is_not_a_commit_is_named_as_such(repo):
    """The third branch of `_require_base_object`, advertised by its own docstring
    and by round 4's commit message, had zero coverage: deleting it entirely failed
    no test, and a tree sha would then have been reported as "not fetched" with a
    fetch command that could not help.
    """
    pp = _load()
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    with pytest.raises(pp.PromptError, match="exists but is not a commit"):
        pp._require_base_object(repo, tree, "main", True)
