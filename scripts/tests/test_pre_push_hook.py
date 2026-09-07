"""Behavioural tests for `scripts/hooks/pre-push`.

The hook had no behavioural coverage before `#706`: `test_init_sh.py` asserts
the SHIM is installed and points at the right engine path, and `test_kitconfig`
asserts the keys it reads exist, but nothing ran the hook and read its exit
code.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

# Engine-relative, never `REPO_ROOT / "scripts"`: those resolve to the same path
# in the kit's own layout and diverge in an adopter's `scripts/devkit` one, which
# is #534 cause 3 and what `test_no_test_module_rebuilds_the_engine_dir_from_repo_root`
# pins. It caught this module's first draft.
ENGINE_DIR = Path(__file__).resolve().parent.parent
HOOK = ENGINE_DIR / "hooks" / "pre-push"
ZERO = "0" * 40
ENGINES = "scripts"


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
            "HOME": str(repo),
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.invalid",
        },
    )
    return done.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "project"
    hook = repo / ENGINES / "hooks" / "pre-push"
    hook.parent.mkdir(parents=True)
    (repo / ENGINES / "lib").mkdir(parents=True, exist_ok=True)
    # The hook resolves kitconfig.py relative to its OWN path, so it must sit
    # where a real install puts it rather than anywhere convenient.
    hook.write_bytes(HOOK.read_bytes())
    hook.chmod(0o755)
    _git(repo.parent, "init", "-q", str(repo))
    return repo


def _commit(repo: Path, message: str = "c") -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _manifest(repo: Path, files: dict[str, bytes], **extra) -> None:
    """Write a manifest recording the CURRENT bytes of each named path."""
    payload = {
        "kit_version": 2,
        "files": {
            path: {"role": "engine", "sha256": hashlib.sha256(body).hexdigest()}
            for path, body in files.items()
        },
        **extra,
    }
    (repo / "kit-manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _push(repo: Path, sha: str, ref: str = "refs/heads/chore/x"):
    return subprocess.run(
        ["bash", f"{ENGINES}/hooks/pre-push", "origin", "https://example.invalid/r.git"],
        cwd=repo,
        input=f"{ref} {sha} {ref} {ZERO}\n",
        capture_output=True,
        text=True,
    )


def test_the_hook_parses_on_its_own():
    """`make check-syntax` cannot establish this, which is `#561`.

    It passes four filenames to ONE `bash -n`, so the first is parsed and the
    rest arrive as that script's positional arguments. `scripts/hooks/pre-push`
    is last on that line, so it is unchecked locally and in CI alike.

    Measured while writing `#706`: `bash -n good.sh bad.sh` exits 0 with a
    broken `bad.sh`. A genuinely unparseable pre-push would therefore reach
    every adopter through a green suite, and it is a hook that runs on every
    push. This test is the one file's worth of that hole closed; `#561` is the
    general fix and stays open.
    """
    done = subprocess.run(["bash", "-n", str(HOOK)], capture_output=True, text=True)

    assert done.returncode == 0, done.stderr


def test_a_stale_manifest_refuses_the_push(tmp_path):
    repo = _repo(tmp_path)
    engine = repo / ENGINES / "kit_doctor.py"
    engine.write_text("print('one')\n", encoding="utf-8")
    _manifest(repo, {f"{ENGINES}/kit_doctor.py": engine.read_bytes()})
    # The edit AFTER the manifest was written — the exact ordering `#706` is
    # filed about.
    engine.write_text("print('two')\n", encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 1, done.stderr
    assert f"{ENGINES}/kit_doctor.py" in done.stderr
    assert "--generate-manifest" in done.stderr


def test_a_current_manifest_allows_the_push(tmp_path):
    repo = _repo(tmp_path)
    engine = repo / ENGINES / "kit_doctor.py"
    engine.write_text("print('one')\n", encoding="utf-8")
    _manifest(repo, {f"{ENGINES}/kit_doctor.py": engine.read_bytes()})
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr
    assert "Refusing to push" not in done.stderr


def test_an_adopter_install_baseline_is_left_alone(tmp_path):
    """`kit_commit` is written only by `--record-install`.

    Against a baseline, a differing hash means the adopter EDITED a kit-owned
    file — a legitimate state. Refusing their push would put `#286`'s bug in a
    new place.
    """
    repo = _repo(tmp_path)
    engine = repo / ENGINES / "kit_doctor.py"
    engine.write_text("print('one')\n", encoding="utf-8")
    _manifest(repo, {f"{ENGINES}/kit_doctor.py": engine.read_bytes()}, kit_commit="abc123")
    engine.write_text("print('adopter edited this')\n", encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr
    # The half this test was missing, and both review lenses found it: exit 0
    # alone passed while the hook warned on EVERY adopter push forever. "Left
    # alone" has to mean quiet, or the name promises more than the body checks.
    assert done.stderr.strip() == "", done.stderr


def test_a_repo_with_no_manifest_is_left_alone(tmp_path):
    repo = _repo(tmp_path)
    (repo / ENGINES / "kit_doctor.py").write_text("print('one')\n", encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr
    # "Left alone" means quiet, the same reading its adopter-baseline sibling
    # already takes. Without this, dropping `SKIP:no-manifest` from the shell's
    # quiet list passes the whole file — measured by a review lens, which
    # mutated exactly that and saw every test still pass.
    assert done.stderr.strip() == "", done.stderr


def test_a_malformed_manifest_does_not_refuse_the_push(tmp_path):
    """Fail open on a manifest that does not parse — but say so.

    Reporting nothing was the first draft, and `#709`'s panel showed why that
    is wrong: an unread manifest means the check did not run, which must not
    look like a check that ran and found nothing.
    """
    repo = _repo(tmp_path)
    (repo / ENGINES / "kit_doctor.py").write_text("print('one')\n", encoding="utf-8")
    (repo / "kit-manifest.json").write_text("{not json", encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr
    assert "could not check kit-manifest.json" in done.stderr


@pytest.mark.parametrize("body", ["[]", "null", "42", '"a string"', "false"])
def test_valid_json_that_is_not_an_object_fails_open_loudly(tmp_path, body):
    """The hole a panel lens found, reproduced against the shipped bytes.

    These parse, so the `ValueError` arm never fires, and every line after it
    assumed a dict — `manifest.get` raised `AttributeError`, `"kit_commit" in
    manifest` raised `TypeError`. The wrapping `2>/dev/null || true` swallowed
    the traceback AND the exit code, so the guard went completely inert while
    printing nothing at all: exit 0, no output, identical to a clean check.

    Both halves are asserted. Exit 0 alone would have passed against the
    defect.
    """
    repo = _repo(tmp_path)
    engine = repo / ENGINES / "kit_doctor.py"
    engine.write_text("print('deliberately stale')\n", encoding="utf-8")
    (repo / "kit-manifest.json").write_text(body, encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr
    assert "could not check kit-manifest.json" in done.stderr, (
        "an unreadable-shape manifest must not go silent — silence here reads "
        "as a clean check"
    )


def test_a_files_table_of_the_wrong_shape_fails_open_loudly(tmp_path):
    repo = _repo(tmp_path)
    (repo / ENGINES / "kit_doctor.py").write_text("print('one')\n", encoding="utf-8")
    (repo / "kit-manifest.json").write_text('{"files": []}', encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr
    assert "could not check kit-manifest.json" in done.stderr


def test_a_clean_check_stays_quiet(tmp_path):
    """The negative half: the warning must follow the failure, not the state
    vocabulary. A guard that warns on every push is one nobody reads.

    Renamed. As `..._and_a_manifestless_repo_both_stay_quiet` it named two cases
    and built one — the manifestless repo has its own test above, which is where
    that half belongs and now asserts the silence itself.
    """
    repo = _repo(tmp_path)
    engine = repo / ENGINES / "kit_doctor.py"
    engine.write_text("print('one')\n", encoding="utf-8")
    _manifest(repo, {f"{ENGINES}/kit_doctor.py": engine.read_bytes()})
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr
    assert done.stderr.strip() == "", done.stderr


def test_a_recorded_file_missing_from_the_commit_is_not_this_checks_business(tmp_path):
    """That is the membership question `#47` owns."""
    repo = _repo(tmp_path)
    engine = repo / ENGINES / "kit_doctor.py"
    engine.write_text("print('one')\n", encoding="utf-8")
    _manifest(
        repo,
        {
            f"{ENGINES}/kit_doctor.py": engine.read_bytes(),
            f"{ENGINES}/gone.py": b"never committed\n",
        },
    )
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr


def test_a_deletion_push_is_not_scanned(tmp_path):
    """A deleted ref has no content to compare."""
    repo = _repo(tmp_path)
    engine = repo / ENGINES / "kit_doctor.py"
    engine.write_text("print('one')\n", encoding="utf-8")
    _manifest(repo, {f"{ENGINES}/kit_doctor.py": engine.read_bytes()})
    engine.write_text("print('two')\n", encoding="utf-8")
    _commit(repo)

    done = _push(repo, ZERO)

    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize("ref", ["refs/heads/chore/x", "refs/heads/dev/y", "refs/heads/main"])
def test_the_guard_applies_to_every_branch(tmp_path, ref):
    """Unlike the narrative guard beside it, this one is not `dev/*`-scoped —
    the occurrences `#706` records were on `chore/*` cockpit branches."""
    repo = _repo(tmp_path)
    engine = repo / ENGINES / "kit_doctor.py"
    engine.write_text("print('one')\n", encoding="utf-8")
    _manifest(repo, {f"{ENGINES}/kit_doctor.py": engine.read_bytes()})
    engine.write_text("print('two')\n", encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha, ref=ref)

    assert done.returncode == 1, done.stderr


def test_a_manifest_entry_with_no_usable_hash_is_reported_not_dropped(tmp_path):
    """Round 1's high, one level down — found again there.

    An entry whose value carries no `sha256` was excluded from the checked set
    and the run still printed `CHECKED`, so a tracked, tampered file went
    unhashed with no signal at all. It does not refuse the push: an unusable
    record is a broken manifest rather than a stale file, and this check cannot
    tell whether those bytes are current. It has to say so.
    """
    repo = _repo(tmp_path)
    good = repo / ENGINES / "kit_doctor.py"
    good.write_text("print('one')\n", encoding="utf-8")
    bad = repo / ENGINES / "other.py"
    bad.write_text("print('two')\n", encoding="utf-8")
    _manifest(repo, {f"{ENGINES}/kit_doctor.py": good.read_bytes()})
    payload = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    payload["files"][f"{ENGINES}/other.py"] = {"role": "engine"}
    (repo / "kit-manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    bad.write_text("print('tampered after the manifest was written')\n", encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 0, done.stderr
    assert "no usable sha256" in done.stderr
    assert f"{ENGINES}/other.py" in done.stderr


def test_every_stale_path_is_indented_not_just_the_first(tmp_path):
    """`printf '    %s\\n' "$one_joined_string"` formats one argument, so the
    format string is never reused and only the first line got its indent."""
    repo = _repo(tmp_path)
    first = repo / ENGINES / "kit_doctor.py"
    second = repo / ENGINES / "other.py"
    first.write_text("print('one')\n", encoding="utf-8")
    second.write_text("print('two')\n", encoding="utf-8")
    _manifest(
        repo,
        {
            f"{ENGINES}/kit_doctor.py": first.read_bytes(),
            f"{ENGINES}/other.py": second.read_bytes(),
        },
    )
    first.write_text("print('edited')\n", encoding="utf-8")
    second.write_text("print('edited too')\n", encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 1, done.stderr
    listed = [
        line for line in done.stderr.splitlines() if line.strip().endswith(".py")
    ]
    assert len(listed) == 2, done.stderr
    assert all(line.startswith("    ") for line in listed), done.stderr


def test_a_newline_in_a_manifest_path_cannot_launder_another_file(tmp_path):
    """The bypass a review lens reproduced end-to-end, pinned.

    `git cat-file --batch` cannot echo the path back, so the reader pairs
    responses with inputs POSITIONALLY. A manifest key carrying a newline
    serialises into two input lines, desynchronising every path after it: the
    next one consumed the wrong chunk, never reached the hash comparison, and
    the hook printed `CHECKED` and exited 0 with no output at all.

    The laundering needs no correct hash for the injected entry, and the target
    keeps its own true recorded hash — so this asserts the refusal still fires
    for the victim, not merely that something was said.
    """
    repo = _repo(tmp_path)
    target = repo / ENGINES / "target.py"
    target.write_text("print('original')\n", encoding="utf-8")
    _manifest(repo, {f"{ENGINES}/target.py": target.read_bytes()})
    payload = json.loads((repo / "kit-manifest.json").read_text(encoding="utf-8"))
    # Sorts immediately before the target, which is what selects the victim.
    payload["files"][f"{ENGINES}/targe\nZZZZ"] = {"sha256": "0" * 64}
    (repo / "kit-manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    target.write_text("print('tampered')\n", encoding="utf-8")
    sha = _commit(repo)

    done = _push(repo, sha)

    assert done.returncode == 1, (
        f"the tampered file was laundered past the guard — {done.stderr!r}"
    )
    assert f"{ENGINES}/target.py" in done.stderr
    assert "no usable sha256" in done.stderr, "the crafted entry must be reported too"
