"""The #428 state guard, at the engine root so every test directory carries it.

WHY THIS FILE EXISTS AT ALL (#428). `pr_watch.py` computes its persistence root
as a module-level constant, evaluated once at import. A test that exercises the
persistence path without individually remembering to redirect it writes straight
into the real ``<repo>/state/pr-watch/`` — the store `pr_watch.py` reads as proof
a review happened, where a fabricated ``fallback:panel`` receipt is
indistinguishable from a real one by the time the merge gate reads it.
``_hermetic_state_root`` in ``tests/conftest.py`` PREVENTS that; this file
DETECTS it, so the next engine to acquire the same import-time-constant habit
trips a loud local failure instead of reopening the hole silently.

WHY THE ENGINE ROOT AND NOT BESIDE THE TESTS (#448). pytest loads conftest.py
from the rootdir down to each collected directory, so one file here is reached by
every test directory under it — ``tests/`` and ``lib/state_paths/tests/`` alike,
and each of them when collected ALONE. Beside the tests it was reached only when
something under ``tests/`` was collected, so `pytest <engine-dir>/lib/state_paths/tests`
by itself carried neither the baseline nor the comparison. Measured on
`09a4c6b` with a leaking test planted in that directory: ``63 passed``, exit 0,
and the write sitting in the live ``state/pr-watch/``.

The two placements #448 weighed both had a defeating objection, and this third
one has neither. A REPO-ROOT conftest guards this repo and reaches no adopter —
the exact failure ``tests/conftest.py``'s own header is about (#33, #112): the
kit's tests are vendored under ``paths.engines`` and collected against the
adopter's rootdir, so anything registered at this repo's root silently does
nothing for them. A SECOND conftest under ``lib/state_paths/tests/`` is a second
copy of a load-bearing guard, kept in step by nothing. The engine root is inside
what an adopter vendors, and is one copy.

MEASURED REACH, rather than reasoned from the loading rule (pytest 9.1.1).
`pytest_sessionfinish` fires whenever pytest actually COLLECTS something inside
this directory or below — `pytest <engine>/tests`, `pytest
<engine>/lib/state_paths/tests`, both directories in one run (the Makefile's
own shape), and a bare `pytest .` at the repo root in the kit's own flat
layout, invoked from the repo root or from inside the engine directory (#495
narrows this from an earlier, broader claim — see below).

NOT GUARANTEED for a bare `pytest .` in a nested ``scripts/devkit/`` adopter
layout (#495). Measured on a real adopter whose ``pyproject.toml`` carried
``testpaths = ["tests"]`` and ``norecursedirs`` including ``scripts/devkit``:
`pytest .` never entered the engine tree at all, so `pytest_sessionfinish`
printed nothing here for it, for a bare `pytest --co` (4556 tests collected),
or for the adopter's full root suite. It fired only for an explicit `pytest
scripts/devkit/tests`. Not a defect in the guard — it does its job wherever
pytest is actually pointed at the engine tree — but an adopter's OWN
``testpaths`` / ``norecursedirs`` can keep a default run out of this directory
entirely, and when that happens this guard does not run at all: no baseline,
no comparison, no tripwire, for that invocation.

WHAT THIS GUARD IS — a tripwire against ACCIDENTAL regressions, the kind the
first paragraph describes: an engine resolving its state path at import time
and leaving a write behind. It is not a defence against a deliberate
adversary, and cannot be: anyone who can pass arbitrary pytest flags
(``--confcutdir=<engine-dir>/tests`` cuts this file off from an otherwise
sanctioned invocation) or plant ``os._exit()`` in a test (no session finish,
no comparison — equally true of SIGKILL and OOM) can just as easily edit this
conftest. Both routes are dispositioned out of scope on #457. The fabricated-
receipt language above says why the STORE is worth guarding, not that this
guard resists fraud.

WHAT IT OBSERVES — the real ``state/`` at TWO INSTANTS: conftest import and
``pytest_sessionfinish``. The bracket is deliberate, not a shortcut, because
``state/`` is a LIVE store: `pr_watch.py` persists into it on every poll, in
ordinary cockpit operation, between and even during test sessions. Only a
change ACROSS THIS SESSION is evidence of a suite defect; any wider window
reads legitimate operation as a leak. Structurally outside its sight,
therefore — the classes, not an enumeration of their members (#457):

  - Anything ALREADY PRESENT at import. A previous run's uncleaned leak is in
    the baseline and reported never again — by then it is indistinguishable
    from legitimate store content to any mechanism that does not track
    provenance, which is also why there is no cross-run baseline: one would
    flag every legitimate `pr_watch` write made between sessions. The banner
    says to clean up immediately, because the next run cannot say anything.
  - Anything NETTING TO ZERO between the instants. A write undone before
    session end leaves no persisted receipt for the merge gate to ever read,
    so the harm the guard exists for did not occur. Watching the interval
    instead — per-test snapshots, write audits — would flag a legitimate
    concurrent writer (a backgrounded `pr_watch.py` poll does exactly this
    during long suites) and trades a fail-closed limitation for a fail-open
    mechanism, the harm `safety-critical-changes.md` rule 3 names.
  - Anything written AFTER the second instant (#460). `pytest_sessionfinish`
    runs before interpreter shutdown, so an ``atexit`` callback registered by
    a test, a surviving non-daemon thread, or a child process that outlives
    the session writes after the comparison has already passed — a green
    run, exit 0, and the write on disk once the process is gone.
    Demonstrated live by #459's round-4 adversarial lens, and pre-existing:
    the bracket has never extended past this hook. Unlike the flag-and-signal
    routes below, this needs no unusual privilege and no visible abnormality,
    so it is tracked as a mechanism decision on #460 rather than disposed as
    adversary-only.

THE REACH RESIDUAL, separate from the observation window above.
**Any run whose CWD is a test directory itself loses the guard** — the boundary
is the working directory, not the argument. An earlier version of this paragraph
said "with no argument", which undersold it; measured, all three of these are
silent on a write into the real ``state/``:

    cd <engine-dir>/tests && pytest                  # rc=0, no banner
    cd <engine-dir>/tests && pytest test_pr_watch.py # rc=0, no banner
    cd <engine-dir>/tests && pytest .                # rc=0, no banner
    cd <engine-dir>/lib/state_paths/tests && pytest  # rc=0, no banner

**Including that last one**, which is the directory #448 was found in and the
one this placement exists to protect. The examples above used to show only
``<engine-dir>/tests``, which read as if the residual were confined to it.

while both of these fire correctly:

    cd <engine-dir> && pytest tests                  # rc=1, banner
    pytest <engine-dir>/tests                        # rc=1, banner

pytest resolves its rootdir — and with it confcutdir — from the cwd and the
arguments together, so standing inside the directory cuts off every conftest
above it however the run is spelled. That whole family carried the guard while
it lived in that directory, so this placement trades a real and ordinary shape
(``cd <engine-dir>/tests && pytest test_x.py -k thing`` while iterating) for a
broad one. **The trade is deliberate and the cost is not zero.** What it buys is
`pytest <engine-dir>/lib/state_paths/tests` from the repo root — which is where
#448 was actually found, and which no placement beside the tests could ever
cover. The sanctioned invocations all name their directories by path: the
Makefile passes both from the repo root, and `adopt.md`/`upgrade.md` tell
adopters to run ``<engine-dir>/tests``. Unlike the flag-and-signal routes
above, this family IS in the threat model — ``cd tests && pytest -k thing``
is ordinary iteration, not adversarial — so closing it is #455, kept its own
change because a second registration point on a load-bearing guard is a new
mechanism, not a fix.

WHY THE ROOT RESOLUTION BELOW IS SELF-CONTAINED, and must stay that way:

  - It cannot import ``tests/_repo_layout.py``. This file has to work in a tree
    that vendors the engines and not the tests; reaching into ``tests/`` for a
    helper would make the guard collapse — at import, aborting collection —
    in precisely that tree.
  - It must not import ``lib/state_paths/repo_root.py`` either, and that is the
    load-bearing half. ``state_paths`` is an ENGINE, and this guard exists to
    catch an engine resolving a state path wrongly. Borrowing an engine's own
    resolution would let the bug being hunted blind the hunter. The duplication
    is the property, not an oversight — ``tests/test_state_guard.py`` pins the
    two resolvers to the same answer so they cannot drift apart unnoticed.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

ENGINE_DIR = Path(__file__).resolve().parent


def _find_repo_root(start: Path) -> Path:
    """The repository root at or above ``start``.

    Walks up for a ``.git`` marker; with none anywhere above, falls back to
    ``start.parent``. Deliberately the same contract as
    ``tests/_repo_layout.find_repo_root``, including the no-marker fallback —
    see the module docstring for why it is a copy rather than an import.
    """
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start.parent


REPO_ROOT = _find_repo_root(ENGINE_DIR)


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_state_snapshot() -> dict[str, str]:
    """``{relpath: recorded kind}`` for every entry under the REAL ``<repo>/state/``.

    The recorded kind is a content hash for a regular file, ``<dir>``,
    ``symlink -> <target>``, or ``<special>`` — the branches below.

    Deliberately independent of ``$DEVKIT_STATE_ROOT`` and of
    ``_hermetic_state_root``: this reads straight off disk at ``REPO_ROOT /
    "state"``, using this file's OWN repo-root resolution — never `pr_watch`'s
    or any other engine's — so a bug in an engine's own root/env resolution
    cannot blind the guard that exists to catch it.

    DIRECTORIES ARE RECORDED TOO, under a trailing-slash key, and that is not
    tidiness. The write this guard is built to catch is an engine resolving its
    state path at import time and then reaching for it — and the first thing
    `pr_watch.py` does on that path is ``STATE_DIR.mkdir(parents=True,
    exist_ok=True)``. A files-only snapshot sees nothing when a suite creates
    ``<repo>/state/<some-new-engine>/`` and writes no file into it, so the very
    next engine to acquire this bug would land in the blind spot rather than
    trip the guard.

    EVERY ENTRY THE WALK YIELDS IS RECORDED AS SOMETHING (#457, #456).
    Symlinks are tested FIRST, because ``is_dir()`` and ``is_file()`` both
    FOLLOW a link: a dangling one used to answer False to both and land in
    neither snapshot (#456), and a live one was recorded as its target's kind,
    so a retarget between two existing files read as no change. A link is
    recorded at its own path with the value ``symlink -> <target path>`` —
    never the target's content, which would miss a retarget to equal bytes,
    block forever on a fifo, and hash a whole tree for a link into a large
    directory; the link itself is the leak. (The kind marker is in the value
    because a key suffix collides — see the comment on the branch below.)
    Anything that is none of link/dir/file — a fifo, a socket, a device
    node — is recorded as ``<special>`` and never read. The root's own
    presence is an entry too (``./``): ``rglob("*")`` yields descendants
    only, so a run that did just ``state.mkdir()`` and wrote nothing below
    it used to compare ``{}`` against ``{}`` (#457).

    Still outside the traversal's sight — the known shapes, stated without
    claiming to be the last:

      - ``state/`` ITSELF BEING A SYMLINK, which the ``is_dir()`` at the top
        of this function follows silently. Nothing in the kit creates one.
      - REPLACEMENT AT A STABLE PATH, for any kind recorded as a CONSTANT. A
        directory or special file deleted and recreated at the same path
        between the two instants compares ``<dir>`` == ``<dir>`` or
        ``<special>`` == ``<special>`` and reads as no change — only files
        (content hash) and symlinks (target path) carry a value that can
        differ. This predates #459 for directories and arrives with the
        ``<special>`` branch for the rest; #459's round-1 adversarial lens
        demonstrated it live with a fifo recreated at its baseline path.

    And what any traversal records is one instant; what the guard can
    conclude from comparing two of them is bounded by the module docstring's
    observation-window section, a different mechanism with its own blind
    spots.
    """
    state_dir = REPO_ROOT / "state"
    if not state_dir.is_dir():
        return {}
    snapshot: dict[str, str] = {"./": "<dir>"}
    for path in sorted(state_dir.rglob("*")):
        relative = str(path.relative_to(state_dir))
        if path.is_symlink():
            # The KIND marker lives in the VALUE, never in a key suffix. `@`
            # is a legal filename character, so a `{relative}@` key collided
            # with a real file literally named `<name>@` — sorted order put
            # the file's hash over the link's entry, and a brand-new symlink
            # beside such a file was invisible (demonstrated live by #459's
            # round-3 adversarial lens). `/` is the one character POSIX
            # forbids in a filename, which is why the directory keys below
            # and the `./` root entry cannot collide with anything; every
            # other kind records at its own path, one entry per path.
            snapshot[relative] = f"symlink -> {os.readlink(path)}"
        elif path.is_dir():
            snapshot[f"{relative}/"] = "<dir>"
        elif path.is_file():
            snapshot[relative] = _hash_file(path)
        else:
            snapshot[relative] = "<special>"
    return snapshot


# The baseline half of the guard, taken HERE — at conftest import — and never
# re-taken. Its partner is `pytest_sessionfinish` below.
#
# WHY IMPORT TIME AND NOT `pytest_sessionstart` (#433 asked for sessionstart).
# `pytest_sessionstart` is not a historic hook — unlike `pytest_configure` — so
# only a plugin already registered when it fires receives it. A conftest is
# registered that early only when it is an INITIAL conftest, and
# `_set_initial_conftests` decides that from the command line: each argument is
# an anchor, plus, for a directory argument, its `test*` SUBDIRECTORIES. So a
# bare `pytest` at the repo root never makes this file initial, and it is then
# imported during collection instead. `pytest_sessionstart` never arrives in
# that shape while `pytest_sessionfinish` still does, so a sessionstart-taken
# baseline would be missing at exactly the moment it is compared.
#
# That is measured, not reasoned: with the baseline moved into
# `pytest_sessionstart` and a leaking test planted in `lib/state_paths/tests`,
# `pytest <repo>` reported four changed paths — three of them files the run
# never touched, hashed identical before and after — because the baseline was
# still its `{}` initial value. The same tree with the baseline taken here
# reported the one path that really changed. (Initialising to `None` instead
# trades that false alarm for a silent miss; both are the same defect.)
#
# Import is the one moment that exists in every invocation shape, and it is
# always before the first test body runs, because pytest completes collection
# (`pytest_collection`) before it enters the run loop (`pytest_runtestloop`) —
# so a conftest reached only during collection is still imported before
# anything executes.
#
# It is deliberately not ALSO refreshed in `pytest_sessionstart`: a baseline
# re-taken later can only absorb writes made in between, which is the exact
# defect #433 is about. Earliest wins, once.
_STATE_BASELINE = _real_state_snapshot()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Regression pin for #428 — load-bearing, not decorative.

    A session hook rather than a session-scoped autouse fixture (#433). A
    fixture's reach was narrower than "the session" because pytest instantiates
    a session-scoped fixture lazily, on the first test that REQUESTS it: `make
    test` runs ``pytest scripts/lib/state_paths/tests scripts/tests`` (paths as
    the Makefile writes them, from the repo root — an earlier version of this
    line dropped both ``scripts/`` prefixes while still claiming to quote the
    command), so the first directory had already run to completion before the
    baseline was taken, and a write into the real ``state/`` originating there
    was absorbed into the baseline instead of caught by it. Hooks have no such lazy step — this one fires once
    per session, for the whole session, and `_STATE_BASELINE` above is taken
    before any test runs at all.

    HOW IT FAILS, AND WHY NOT BY RAISING. The two obvious forms were measured
    on pytest 9.1.1 rather than reasoned about, and both are worse than what is
    written here:

      - `assert` / `raise`. `wrap_session` calls this hook from inside its own
        ``finally``, outside every ``except`` it has, so the exception escapes
        ``python -m pytest`` entirely: 62 lines of runpy/pluggy traceback, no
        test summary of any kind, and the actual message on the last line. It
        reads as pytest having crashed, not as a guard firing.
      - ``pytest.exit(msg, returncode=1)``. Caught cleanly by `wrap_session`
        and it does set the exit code — but it unwinds through the terminal
        reporter's OWN ``pytest_sessionfinish`` wrapper before that wrapper can
        print, so the whole FAILURES section and short summary are suppressed.
        Measured with a deliberately failing test alongside: the run printed
        ``.F`` and one ``Exit:`` line, and the real failure was never reported.
        A guard that hides other failures is worse than the leak it catches.

    So: set the two attributes the reporter and `wrap_session` already read.
    ``session.exitstatus`` is returned by `wrap_session` AFTER its ``finally``
    completes, so assigning it here is what turns the process red;
    ``session.shouldfail`` is printed by the terminal reporter as a red ``!!!!``
    banner in the last position before the stats line, which is the only
    tail-most slot a plugin can reach (``pytest_terminal_summary`` runs
    earlier). Normal reporting is left completely intact, verified the same way
    — a real failure alongside the guard still prints its FAILURES section and
    its ``FAILED`` line.

    The one residual: on an otherwise all-passing run the final stats line still
    reads ``N passed``, because nothing here fabricates a test report to make it
    say otherwise. The red banner directly above it and the non-zero exit are
    what carry the verdict — `make test` stops with ``Error 1``.
    """
    after = _real_state_snapshot()
    if after == _STATE_BASELINE:
        return
    changed = sorted(
        rel
        for rel in set(_STATE_BASELINE) | set(after)
        if _STATE_BASELINE.get(rel) != after.get(rel)
    )
    # Two lengths on purpose. The banner goes through `write_sep`, which pads to
    # the terminal width, so the changed-path list — unbounded, one entry per
    # leaked file — stays out of it and goes in the section body instead.
    summary = f"REGRESSION (#428): the suite wrote into the real {REPO_ROOT / 'state'}"
    detail = (
        f"{summary} during this run instead of staying inside the per-test "
        "$DEVKIT_STATE_ROOT sandbox that _hermetic_state_root (tests/conftest.py) "
        f"sets. Changed paths: {changed}. Clean these up NOW: this report is "
        "one-shot — a leak still on disk at the next run's conftest import is "
        "absorbed into that run's baseline and never reported again (#457)."
    )
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_sep("=", "REAL state/ WAS WRITTEN (#428)", red=True, bold=True)
        reporter.write_line(detail)
    else:
        # `-p no:terminal`, or any other run with the reporter unregistered.
        # The verdict must survive the message having nowhere to go.
        print(detail, file=sys.stderr)
    session.shouldfail = summary
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
