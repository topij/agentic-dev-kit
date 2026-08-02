#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Report how far an adopting repo has drifted from the kit it was installed from.

The upgrade problem this exists to solve: an adopter's copy of the kit has no
version marker on its *engines* and no record of whether they were edited. Real
installs surveyed before this was written spanned four shapes — an ancestor with
no config surface at all, a v1-schema repo with only two of six engines and a
`paths.engines` value that pointed at the wrong directory, a correctly namespaced
v2 repo, and the template itself — and nothing could tell them apart. One repo's
``pr_watch.py`` was three features behind upstream and nobody knew.

So: **engines are kit-owned, config is adopter-owned.** That invariant is what
makes an upgrade a file copy instead of a manual merge, and this script is what
verifies it still holds. Per kit-owned file it reports one of:

``unchanged``
    Byte-identical to the manifest. Safe to replace outright on upgrade.
``differs``
    Present but not byte-identical to the manifest. A hash mismatch cannot
    distinguish "older kit version" from "hand-edited", so this deliberately
    does NOT claim which — calling an old file "locally modified" sends someone
    hunting for edits they never made. The report narrows it using the config's
    schema version, and either way the required action is the same: diff before
    replacing, never clobber.
``missing``
    Not installed, and nothing installed here needs it. Either a deliberately
    sized-down adoption or an incomplete one; the report can't tell, so it says
    so rather than guessing.
``missing-required``
    Not installed, but an engine that IS installed needs it — so this install
    is broken, not sized down. The distinction exists because the old report had
    only ``missing``, which files a hard dependency under "sized-down adoption,
    or incomplete" alongside `docs/templates/*.tmpl`, which genuinely are
    optional. `/upgrade` then tells the operator that a missing piece may be a
    deliberate omission and to ask before installing it — so the documented path
    invited someone to decline `lib/kitconfig.py`, which every Python engine
    imports (issue #41). Which files these are is DERIVED at
    ``--generate-manifest`` time from the dependency graph — Python imports and
    shell ``source`` — not restated by hand.
``unknown-version``
    The manifest has no entry for this file, so drift can't be judged.

Adopter-owned paths (the config, the narrative docs) are **never** compared —
they are supposed to differ, and reporting them as drift would bury the signal.

`paths.engines` indirection is handled: the manifest records the kit's own
layout (``scripts/…``), and comparison maps that prefix onto whatever the
adopter configured, so a repo that vendored engines under ``scripts/devkit/``
compares correctly without a rewritten manifest.

Read-only. Never writes to the repo it inspects (``--generate-manifest`` writes
only the manifest, and only when run in the kit's own checkout).

Usage:
    uv run scripts/kit_doctor.py                    # human report
    uv run scripts/kit_doctor.py --json             # machine-readable
    uv run scripts/kit_doctor.py --generate-manifest  # (kit repo) refresh the manifest

Exit codes:
    0 — every kit-owned file is `unchanged` (or intentionally absent)
    1 — at least one file `differs`, is `unknown-version`, or is
        `missing-required`. The last one is not drift, but it is a broken
        install, and the exit code an adopter gates CI on should not be green
        for a tree whose engines cannot load their own library.
    2 — usage error (no config, no manifest, unreadable input) — including a
        `kit.version` that is present but not a number. That is deliberately
        NOT a warning-and-exit-0: CI gates on this exit code, and a config the
        report itself calls UNREADABLE must not pass a gate.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import posixpath
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from kitconfig import get, load_config, repo_root  # noqa: E402

MANIFEST_NAME = "kit-manifest.json"

# Files the KIT owns, as they sit in the kit's own tree. An adopter should never
# need to edit one of these — everything project-specific belongs in
# config/dev-model.yaml. `role` groups the report; `engine_relative` marks the
# paths that move with `paths.engines`.
KIT_OWNED: tuple[tuple[str, str], ...] = (
    # engines (move with paths.engines)
    ("scripts/pr_watch.py", "engine"),
    ("scripts/check_doc_budget.py", "engine"),
    ("scripts/archive_plan_sessions.py", "engine"),
    ("scripts/dev_session.sh", "engine"),
    ("scripts/reconcile_sessions.sh", "engine"),
    ("scripts/kit_doctor.py", "engine"),
    # Assembles panel launch prompts by QUOTING the contract out of
    # docs/agentic-dev-kit/fallback-review-panel.md at run time (#214). That
    # coupling is why it is tracked beside the doctrine rather than left
    # adopter-local: an /upgrade that refreshed the doctrine and not this engine
    # would leave the parser pointed at a heading that moved, and the engine
    # exits 2 rather than guessing — a hard failure at panel time, which is the
    # worst moment for one.
    ("scripts/panel_prompt.py", "engine"),
    ("scripts/lib/kitconfig.py", "engine"),
    ("scripts/lib/atomic_write.py", "engine"),
    ("scripts/lib/devmodel_config.py", "engine"),
    ("scripts/lib/repo_root.sh", "engine"),
    ("scripts/lib/state_paths/__init__.py", "engine"),
    ("scripts/lib/state_paths/resolver.py", "engine"),
    ("scripts/lib/state_paths/paths.py", "engine"),
    ("scripts/lib/state_paths/repo_root.py", "engine"),
    # Shipped, imports kitconfig, and was untracked until #37 — so an upgrade
    # refreshed every engine around it and left this one at whatever version
    # the adopter first installed, while reporting `0 differ, 0 unknown`.
    ("scripts/check_memory_budget.py", "engine"),
    ("scripts/hooks/pre-push", "hook"),
    # Same omission as check_memory_budget.py, and the more consequential half:
    # this hook reads `review.fallback_panel.lens_compute` to render the
    # panel reminder, so an adopter whose copy predates that key gets a
    # reminder naming compute the kit no longer prescribes — silently, because
    # an untracked file cannot differ.
    ("scripts/hooks/pr_followup_hook.py", "hook"),
    # shared workflow definitions
    ("docs/agentic-dev-kit/workflows/session-start.md", "workflow"),
    ("docs/agentic-dev-kit/workflows/wrap-up.md", "workflow"),
    ("docs/agentic-dev-kit/workflows/pr-watch.md", "workflow"),
    ("docs/agentic-dev-kit/workflows/parallel.md", "workflow"),
    # Tracked for exactly the reason fallback-review-panel.md is (see below):
    # parallel.md is manifest-owned and /upgrade-refreshed, and links here
    # THREE times — once to say the lane-contract preamble now lives in this
    # file. Untracked, an upgrade installed those links and not their target,
    # and reported a clean bill of health. That is #146, and it is the concrete
    # occurrence behind #37: the untracked file was the target of a link from a
    # tracked one, so refreshing the tracked file is what created the dangling
    # reference. Tracking this file closes that instance and NOTHING MORE: no
    # test detects the same pairing for the next doc, so a new link from a
    # tracked file to an untracked one reproduces #146 exactly. A guard for it
    # was built here and reverted — see #216 for why and for the design. Do not
    # read this entry as the class being handled.
    ("docs/agentic-dev-kit/workflows/parallel-headless.md", "workflow"),
    ("docs/agentic-dev-kit/safety-critical-changes.md", "doctrine"),
    # Tracked because safety-critical-changes.md — which IS refreshed by
    # /upgrade — links to it from rules 2 and 3. An untracked target means an
    # upgrading adopter gets doctrine pointing at a file they do not have, and
    # kit_doctor cannot report it missing because it is not tracked.
    ("docs/agentic-dev-kit/fallback-review-panel.md", "doctrine"),
    # The companion split out of the file above (#213). Tracked for the SAME
    # reason and by the same hand-checked route: fallback-review-panel.md is
    # manifest-owned and /upgrade-refreshed, and links here once. Untracked,
    # an upgrade would refresh that link and not its target — #146 exactly,
    # reproduced by the very change that split the file. NOTHING IN THE SUITE
    # ENFORCES THIS PAIRING: the link guard was built and reverted (#216), so
    # this entry and the kit-manifest.json entry beside it are a manual
    # checklist item. If you add another kit doc linked from a tracked one,
    # you must do this by hand too.
    ("docs/agentic-dev-kit/fallback-review-panel-evidence.md", "doctrine"),
    # Tracked so an adopter who installs the kit gets it, and so kit_doctor can
    # say when they did not. NOT for the same reason as the line above, despite
    # an earlier version of this comment claiming so: fallback-review-panel.md
    # is linked from safety-critical-changes.md, which is itself manifest-owned
    # and /upgrade-refreshed, so an untracked target would leave *shipped*
    # doctrine dangling. This file's referrers (/adopt, ruff.toml, the ruff CI
    # step) are none of them manifest-owned, so nothing shipped would dangle —
    # the argument for tracking it is simply that it is doctrine an adopter
    # needs, and it is the only surface that explains the engines-dir exclusion.
    # (/upgrade does not mention it at all; the earlier comment said it did.)
    ("docs/agentic-dev-kit/adopting-into-a-linted-repo.md", "doctrine"),
    # narrative-doc templates (the rendered outputs are adopter-owned)
    ("docs/templates/handoff.md.tmpl", "template"),
    ("docs/templates/handoff-history.md.tmpl", "template"),
    ("docs/templates/friction-log.md.tmpl", "template"),
    ("docs/templates/friction-log-archive.md.tmpl", "template"),
    # The AGENTS.md entry point renders from this (#92). Only the TEMPLATE is
    # kit-owned: the rendered root AGENTS.md is the adopter's to extend, so it
    # is listed in ADOPTER_OWNED below instead.
    ("docs/templates/AGENTS.md.tmpl", "template"),
)

# Paths that are the ADOPTER's — expected to differ, never reported as drift.
# Listed explicitly (rather than inferred) so the boundary is auditable, and so
# an installer can consume the same list to decide what not to copy.
ADOPTER_OWNED: tuple[str, ...] = (
    "config/dev-model.yaml",
    "docs/handoff.md",
    "docs/handoff-history.md",
    "docs/friction-log.md",
    "docs/friction-log-archive.md",
    # Rendered from docs/templates/AGENTS.md.tmpl; unlike an engine it is meant
    # to be edited, so it must never be reported as drift.
    "AGENTS.md",
    # This repo's own narrative files (see the note in config/dev-model.yaml).
    "docs/kit-handoff.md",
    "docs/kit-handoff-history.md",
    "docs/kit-friction-log.md",
    "docs/kit-friction-log-archive.md",
    "README.md",
    ".gitignore",
)

# `paths.engines` default in the kit's own layout — the prefix remapped onto an
# adopter's configured engines directory.
KIT_ENGINE_PREFIX = "scripts"


def _derive_engine_names(kit_owned: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    """Engine paths as they sit UNDER `paths.engines`, derived from KIT_OWNED.

    Used to probe whether a configured engines directory holds anything at all.
    DERIVED rather than restated: this used to be a hardcoded triple
    (check_doc_budget.py, pr_watch.py, dev_session.sh), so a deliberately
    sized-down install containing only kit_doctor.py and lib/kitconfig.py
    reported "contains no kit engine" — from inside the very directory it was
    executing out of, while the same run counted those two files as
    ``unchanged`` (issue #59).

    Entries outside ``KIT_ENGINE_PREFIX`` are skipped: their location under an
    adopter's engines dir is not derivable by a prefix swap, so including one
    would make the probe stat a path no layout produces. Nothing in KIT_OWNED
    is outside the prefix today; the rule is here so that adding such an entry
    cannot silently produce a garbage probe path.

    ``init.sh``'s ``detect_engines_dir()`` used to carry the identical triple —
    the write-side half of the same bug (issue #67); it now derives its probe
    list from the manifest this tuple generates, filtered to top-level engine
    names (its detection must not match an adopter's own generic ``lib/`` file;
    this probe checks a directory the adopter already configured, so it keeps
    them). #47 tracks deriving KIT_OWNED itself from the shipped tree, which
    subsumes the remaining restatements.
    """
    return tuple(
        rel[len(KIT_ENGINE_PREFIX) + 1 :]
        for rel, role in kit_owned
        if role == "engine" and rel.startswith(KIT_ENGINE_PREFIX + "/")
    )


_ENGINE_NAMES: tuple[str, ...] = _derive_engine_names(KIT_OWNED)

# Import statements in a file Python cannot parse. Applied ONLY to `engine` and
# `hook` roles, never to docs or templates: markdown cannot import anything, and
# a doctrine file quoting `from kitconfig import get` inside a code fence would
# otherwise manufacture a dependency edge out of prose. Its user is
# `scripts/hooks/pre-push`, a bash file whose kitconfig import lives inside a
# `python3 - <<'PY'` heredoc.
_TEXT_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_.]*)", re.MULTILINE)

# Bash `source` / `.` of another kit file. A shell engine's dependency is a PATH,
# not a module name, so it needs its own scanner — and without one the graph
# fails open on exactly the pair #41 is about: `dev_session.sh` and
# `reconcile_sessions.sh` both `source "$SCRIPT_DIR/lib/repo_root.sh"`, so a tree
# missing `lib/repo_root.sh` reported `0 missing`-that-matters and exit 0 while
# `bash scripts/dev_session.sh` died on line 63. The Python-only version of this
# function shipped that hole and the /upgrade wording built on it went further
# than the text it replaced — "declining one is safe" — which is a worse false
# assurance than the "decide, don't assume" it superseded. Found by the
# adversarial lens on PR #225.
# The operand: a double-quoted string, a single-quoted string, or a bare word.
# The double-quoted alternative admits `$( … )` chunks explicitly, because
# `"$(dirname "$0")/lib/x.sh"` — the commonest form of this idiom — nests a
# quote INSIDE the quoted operand, and a plain `"[^"]*"` truncates it to
# `"$(dirname "`.
#
# The BARE alternative stops at a shell separator rather than at whitespace:
# `{ source lib/dep.sh; }` and `source lib/dep.sh; cat <<EOF` otherwise yield
# `lib/dep.sh;` with the semicolon attached, which `_NOT_A_LITERAL_PATH` does
# not reject (`;` is not in its class) and which therefore reaches `record()`
# as a path that can never match. Found by probing this function's own new
# separator handling, not by a lens.
_OPERAND = r"""(?:"((?:\$\([^)]*\)|[^"])*)"|'([^']*)'|([^\s;&|<>]+))"""

# `source` must be the FIRST token on its line. This is a deliberate,
# re-affirmed bound, not an oversight — and the history is worth keeping because
# the obvious improvement was tried and withdrawn:
#
# Round 2 widened it to match after a separator or block keyword, so that
# `[ -f "$LIB" ] && source "$LIB"` would be seen. Round 3 showed what that cost.
# The scan reads raw text and has no notion of "inside a string", so
# `echo "please then source lib/dep.sh now"` — ordinary prose in an ordinary
# echo — produced a real dependency edge. That is the harmful direction: a bogus
# `required_by` in the manifest tells an adopter whose install is FINE that it is
# broken and to install a file they do not need, which is `missing-required`
# firing in reverse.
#
# Deciding command position correctly needs a bash tokenizer — quote state,
# escapes, `$'…'`, line continuations, multi-line strings — and every regex
# approximation of it found in three rounds leaked in one direction or the
# other. Anchoring has exactly ONE failure direction, and it is the safe one: a
# guarded `source` is missed, which degrades that file to plain `missing`, i.e.
# the pre-#41 behaviour. Unhelpful, never misleading. Both shell engines in this
# tree use the anchored form, so nothing real is missed today; #228 holds the
# proper fix. The miss is pinned by a test so it stays a stated bound.
_SOURCE_RE = re.compile(r"^[ \t]*(?:source|\.)[ \t]+" + _OPERAND)

# `<<DELIM`, `<<'DELIM'`, `<<-DELIM`. Heredoc BODIES are skipped by the shell
# scanner (and only by it): a `source` line inside a heredoc is text being
# printed, not a dependency. `pre-push` already carries two `cat >&2 <<EOF`
# help blocks, and one of them gaining a line explaining how a sibling engine
# wires itself up would have baked a false edge into the manifest — telling
# every adopter with the hook and without the session engines that their
# install is broken. Note the Python-import scan deliberately does NOT skip
# heredocs: `pre-push`'s kitconfig import lives inside a `python3 - <<'PY'`
# body and genuinely executes. Adversarial lens, PR #225 round 2.
#
# The `<` guards are load-bearing and were missing at first: `<<<` is a
# HERESTRING with no body, but an unguarded `<<-?` matched its second and third
# characters and took the following word as a delimiter — so `read x <<< "$out"`
# put the scanner into a heredoc that never closed, silently deleting every real
# edge for the REST OF THE FILE. That is strictly worse than the false positive
# the heredoc skip was added to fix, and the pre-round-2 code got it right by
# having no heredoc concept at all. Adversarial lens, PR #225 round 3.
_HEREDOC_RE = re.compile(r"(?<!<)<<(?!<)-?[ \t]*[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?")

# A leading shell expansion — `$SCRIPT_DIR/`, `${VAR}/`, `$(dirname "$0")/` —
# stripped so what remains is a path relative to the sourcing file's own
# directory, which is what every such prefix in this tree resolves to.
_SHELL_PREFIX_RE = re.compile(r"^(?:\$\([^)]*\)|\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*)/")

# What is left must be a literal relative path. Anything still carrying a shell
# metacharacter is computed at run time, and the honest answer there is no edge
# rather than a guessed one.
#
# NOT INDEPENDENTLY PINNABLE, and recorded as such rather than left looking like
# tested behaviour: `record()` already requires an exact match against
# KIT_OWNED, so a candidate this filter rejects would be discarded there anyway
# — deleting the filter changes no observable output and fails no test. It is
# kept as the second of two checks because the operand capture is deliberately
# permissive, and it states an intent `record()`'s membership test does not.
# Adversarial lens, PR #225 round 2; the backtick was added to the class in the
# same round, since a single-token `source \`depfile\`` slipped through a class
# whose whole job is rejecting substitutions.
_NOT_A_LITERAL_PATH = re.compile(r"""[\s$`"'*?\[\]{}()|&<>]""")


def _imported_modules(text: str) -> set[tuple[int, str]]:
    """``(relative_level, dotted_name)`` for every import in `text`.

    `ast` first, and the choice matters rather than being stylistic: two library
    modules here open with a usage example in the module docstring — the literal
    line ``from devmodel_config import get, load_config, resolve_path`` sits in
    `devmodel_config.py`'s own docstring. A text scan reads that as an import
    and marks the module required by itself; `ast` sees a string constant. The
    regex is the fallback for files Python cannot parse at all.
    """
    modules: set[tuple[int, str]] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {(0, m.group(1)) for m in _TEXT_IMPORT_RE.finditer(text)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update((0, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add((node.level, node.module))
            elif node.level:
                # `from . import resolver` — the imported NAME is the module.
                modules.update((node.level, alias.name) for alias in node.names)
    return modules


def _module_targets(module: str, package_dir: str) -> tuple[str, ...]:
    """Kit-layout paths a dotted module name could resolve to under `package_dir`."""
    base = "/".join(module.split("."))
    return (f"{package_dir}/{base}.py", f"{package_dir}/{base}/__init__.py")


def _heredoc_body_lines(lines: list[str]) -> set[int]:
    """Indices of lines inside a heredoc body — but only for bodies that CLOSE.

    The two-pass shape is the point, and it is a structural bound rather than
    another regex patch. A single-pass tracker treats a mis-detected opener as
    the start of a body that runs to end of file, so ONE false positive deletes
    every real dependency edge after it. Three separate constructs were found
    tripping that in one review round — `<<<` herestrings, and `<<` inside
    `$(( … ))` arithmetic, both of which look exactly like `<<DELIM` to a regex.
    `dev_session.sh` already contains eight herestrings and is safe today only
    because each happens to be followed by `"$…` rather than a bare word.

    Requiring the delimiter to actually appear on a later line turns every such
    mis-detection into a NO-OP: a bogus delimiter (`greeting`, `shift_amount`)
    essentially never occurs as a standalone line, so the region is discarded
    and those lines are scanned normally. The failure mode stops scaling with
    file length, which is what made the single-pass version dangerous rather
    than merely imprecise. Adversarial and correctness lenses, PR #225 round 3.
    """
    body: set[int] = set()
    index = 0
    while index < len(lines):
        opening = _HEREDOC_RE.search(lines[index])
        if not opening:
            index += 1
            continue
        delimiter = opening.group(1)
        for close in range(index + 1, len(lines)):
            if lines[close].strip() == delimiter:
                body.update(range(index + 1, close))
                index = close
                break
        # No terminator: not a heredoc at all. Fall through WITHOUT consuming,
        # so the very next line is examined normally.
        index += 1
    return body


def _sourced_paths(text: str, rel: str) -> set[str]:
    """Kit-layout paths this shell file `source`s, resolved against its own dir.

    Only the leading shell expansion is stripped; a `source` whose path is
    genuinely computed at run time (a loop variable, a value read from config)
    resolves to nothing and produces no edge. Nothing in the tree does that
    today, and no test here would catch a future engine that did — the same
    stated limit `derive_dependencies` records for dynamic Python imports.

    Heredoc bodies are skipped: a `source` line inside one is text being
    printed, not a dependency. The line that OPENS a heredoc is ordinary code
    and is still scanned.
    """
    here = PurePosixPath(rel).parent
    found: set[str] = set()
    lines = text.splitlines()
    skip = _heredoc_body_lines(lines)
    for number, line in enumerate(lines):
        if number in skip:
            continue
        # No comment stripping: with `source` anchored to the first token, a
        # commented line cannot match in the first place — `#` is not `source`.
        # Round 2 carried a `_COMMENT_RE` because the widened anchor could reach
        # a `source` after a `&&` INSIDE a comment; withdrawing that widening
        # removed the only thing it defended against, and keeping a guard whose
        # justification no longer holds is how dead code acquires authority.
        # The commented-out-source tests still pass, now via the anchor.
        for match in _SOURCE_RE.finditer(line):
            quoted_double, quoted_single, bare = match.groups()
            operand = next(g for g in (quoted_double, quoted_single, bare) if g is not None)
            tail = _SHELL_PREFIX_RE.sub("", operand)
            if not tail or tail.startswith("/") or _NOT_A_LITERAL_PATH.search(tail):
                continue
            # normpath, not a bare join: `PurePosixPath` does NOT collapse `..`,
            # so `scripts/sub` / `../lib/dep.sh` stayed `scripts/sub/../lib/dep.sh`
            # and could never equal the canonical KIT_OWNED path it genuinely
            # names — a literal, unconditional dependency dropped in silence.
            # That is #41's own failure class reached by a different route, and
            # it is NOT the documented "computed at run time" bound: nothing
            # here is computed. Correctness lens, PR #225 round 2.
            target = posixpath.normpath(str(here / tail))
            # A path that climbs out of the repo cannot name a KIT_OWNED file;
            # recording it would put `../…` in the manifest.
            if target.startswith(".."):
                continue
            found.add(target)
    return found


def derive_dependencies(
    root: Path, kit_owned: tuple[tuple[str, str], ...] = KIT_OWNED
) -> dict[str, list[str]]:
    """Map each kit-owned file to the kit-owned files that import it.

    This is the ``required`` axis #41 asks for, DERIVED rather than declared —
    for the same reason `_derive_engine_names` is derived (#59, #67): a
    hand-maintained list of hard dependencies goes stale exactly when a new
    engine starts importing something, which is the moment it needed to be
    right. A boolean would also be less true than this mapping. "Required" is
    not a property of a file, it is a property of a PAIR: `lib/kitconfig.py`
    matters to a repo that installed an engine and does not matter to one that
    installed none, and both are supported adoptions.

    Resolution mirrors what the engines actually do at run time: every Python
    one does ``sys.path.insert(0, <engine-dir>/"lib")`` before importing, so an
    absolute import resolves against ``scripts/lib``. Relative imports resolve
    against the importing file's own package, which is what keeps the
    `state_paths` package's internal edges (``from .resolver import …``) in the
    graph rather than only its top-level name.

    **The shell engines are scanned too, and must be.** `dev_session.sh` and
    `reconcile_sessions.sh` `source "$SCRIPT_DIR/lib/repo_root.sh"`, which is a
    hard dependency expressed as a path rather than a module. A Python-only
    version of this function reported such a tree exit-0 clean while
    ``bash scripts/dev_session.sh`` died on its `source` line — #41's own bug
    class, reproduced by the change meant to close it. `.py` files take the
    `ast` path and only that; everything else is scanned for both Python-style
    imports (the `pre-push` heredoc) and shell `source`.

    LIMITS, because a graph that overstates its coverage is worse than a short
    one:

    - Only `engine` and `hook` roles are scanned; see `_TEXT_IMPORT_RE`.
    - Only imports resolving to a KIT_OWNED path are recorded. Third-party and
      stdlib imports are not this function's business, and an engine importing
      an UNTRACKED kit file produces no edge at all — that is #37's class, not
      one this can see.
    - A dynamic import (``importlib``, an ``__import__`` call) is invisible, as
      is a `source` whose path is computed at run time. No file THIS FUNCTION
      SCANS does either today; the qualifier is load-bearing, because several
      TEST modules do use `importlib.util`, and they are neither `engine` nor
      `hook` so they are out of scope. A future ENGINE that did either would get
      a silently thin graph, and no test here would catch it.

      This sentence has now been wrong twice — first claiming "nothing in the
      tree does this", then naming three test modules when there are four — so
      it no longer enumerates them. `grep -rln importlib scripts/` is the
      answer, and unlike a list in a docstring it cannot go stale.
      (Correctness lens, PR #225 rounds 1 and 2.)
    - The shell scan requires `source` to be the FIRST token on its line. A
      guarded (`[ -f "$L" ] && source "$L"`), nested, continued, or
      `eval`-reached `source` is not seen. Widening this was tried in round 2
      and withdrawn in round 3: without a bash tokenizer the widened form could
      not tell a command position from the word `then` inside a string, and
      manufactured edges out of prose. #228 holds the proper fix.

      Of these, the GUARDED and NESTED forms are pinned by a test so they stay
      stated rather than implicit. The continuation, `eval` and shell-function
      forms are NOT pinned by anything — said plainly because an earlier version
      of this paragraph claimed "both directions of this bound are now pinned by
      tests", which the correctness lens checked and found false: `grep -n
      "continuation\\|eval" scripts/tests/test_kit_doctor.py` returns nothing.
    - Every one of these bounds errs toward NO edge. That direction is chosen,
      not incidental: a missing edge degrades a file to plain `missing`, which
      is the pre-#41 behaviour and merely unhelpful, while a false edge tells an
      adopter their working install is broken and to install something they do
      not need. `missing-required` firing wrongly is worse than it not firing.
    """
    owned = {rel for rel, _ in kit_owned}
    dependents: dict[str, set[str]] = {}

    def record(target: str, importer: str) -> None:
        if target in owned and target != importer:
            dependents.setdefault(target, set()).add(importer)

    for rel, role in kit_owned:
        if role not in ("engine", "hook"):
            continue
        source = root / rel
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        for level, module in _imported_modules(text):
            if level:
                package = PurePosixPath(rel).parent
                for _ in range(level - 1):
                    package = package.parent
                package_dir = str(package)
            else:
                package_dir = f"{KIT_ENGINE_PREFIX}/lib"
            for candidate in _module_targets(module, package_dir):
                record(candidate, rel)
        # Dispatched on the SUFFIX, not on whether `ast` happened to succeed: a
        # short shell file can be accidentally valid Python, and resting a
        # correctness property on "bash never parses" is the kind of implicit
        # bound this report exists to avoid.
        if not rel.endswith(".py"):
            for candidate in _sourced_paths(text, rel):
                record(candidate, rel)
    return {path: sorted(deps) for path, deps in sorted(dependents.items())}


@dataclass
class FileStatus:
    path: str
    role: str
    state: str
    detail: str = ""


@dataclass
class Report:
    kit_version_config: int | None
    kit_version_manifest: int | None
    engines_dir: str
    engines_dir_ok: bool
    hooks_installed: bool
    narrative_rendered: dict[str, bool]
    # The version values as they were actually written, so the report can tell
    # "a version key that is not a number" (a typo — do not migrate) apart from
    # "no usable version" (pre-v2 — do migrate). Both leave the parsed field at
    # None, and conflating them sends an adopter with `version: v2` into a
    # migration they do not need.
    #
    # LIMIT, because the sentinel is `raw is not None`: an explicit `version:`
    # / `version: null` / `version: ~` resolves to None and is therefore
    # indistinguishable from an absent key. All three render as UNVERSIONED.
    # That is the right advice for an absent key and merely imprecise for a null
    # one, so it is recorded rather than worked around — a second sentinel would
    # be a value that config parsing cannot currently produce.
    kit_version_config_raw: object = None
    kit_version_manifest_raw: object = None
    files: list[FileStatus] = field(default_factory=list)

    @property
    def drifted(self) -> list[FileStatus]:
        return [f for f in self.files if f.state in ("differs", "unknown-version")]

    @property
    def missing(self) -> list[FileStatus]:
        return [f for f in self.files if f.state == "missing"]

    @property
    def broken(self) -> list[FileStatus]:
        """Files an installed engine needs and that are not installed.

        Deliberately NOT folded into `drifted`: a file that is absent has not
        drifted from anything, and this report's whole position is that it does
        not claim more than it knows. They meet only at the exit code.
        """
        return [f for f in self.files if f.state == "missing-required"]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_version(value: object) -> int | None:
    """Read a schema version from config or manifest; None if it isn't one.

    ``kitconfig`` coerces UNQUOTED integers only — deliberately, because that is
    what PyYAML does — so ``version: "2"`` arrives here as the string ``"2"``
    and the ``cfg_v < man_v`` comparison in `render` raised ``TypeError: '<' not
    supported between instances of 'str' and 'int'`` (issue #61). Quoting a
    scalar is an ordinary thing for a YAML author to do, and a *read-only
    diagnostic* answering it with a traceback tells the adopter the doctor is
    broken rather than their config. Coercing here rather than in ``kitconfig``
    keeps that module's PyYAML parity intact — the divergence would be the bug.

    Dispatched on type rather than run through ``int(str(value))``, because that
    shorter form is looser than "a schema version": ``int()`` accepts Python's
    underscore separators and any Unicode decimal digit, so a QUOTED
    ``version: "1_0"`` would become a confident, silent **10** and ``"２"``
    would become 2 — values no YAML parser produced.

    **Scope, precisely.** This only filters values `kitconfig` handed over as a
    ``str``, i.e. ones the author quoted. An UNQUOTED ``version: 1_0`` is
    resolved to the int 10 by `kitconfig` — and by PyYAML, since YAML 1.1
    genuinely permits underscore separators in integers — so it arrives here as
    a plain ``int`` and is passed through. That is correct: second-guessing a
    value YAML itself resolved is not this function's job. (`kitconfig` does
    diverge from PyYAML on unquoted non-ASCII digits, where PyYAML yields a
    ``str``; that belongs to `kitconfig`'s parity tests, not here.)

    ``bool`` is rejected first and explicitly: it is an ``int`` subclass, so the
    ``isinstance(value, int)`` branch below would otherwise read ``version:
    true`` as schema v1.

    A ``float`` that is integral is accepted (``2.0`` → 2) only because the code
    this replaced handled it and rejecting it would make a plausible YAML
    spelling strictly worse than before the fix. A leading sign is accepted on
    the ``str`` branch so that quoted and unquoted spellings of the same value
    agree — the report tells adopters they are equivalent.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        text = value.strip()
        # A leading sign is part of the number, not of the digits. Sliced with
        # an explicit tuple: `text[:1] in "+-"` is True for the empty string.
        digits = text[1:] if text[:1] in ("+", "-") else text
        # `isascii()` rejects Unicode decimal digits; `isdigit()` rejects the
        # `1_0` underscore form that bare `int()` would silently accept. Both
        # are False for "", so a bare sign or an empty value falls through.
        return int(text) if digits.isascii() and digits.isdigit() else None
    return None


def _hook_dirs(root: Path):
    """Every directory git might read hooks from, honoring ``core.hooksPath``.

    ``$GIT_DIR/hooks`` is not the only answer: ``core.hooksPath`` overrides it,
    and pre-commit plus several monorepo layouts set it. Checking only
    ``.git/hooks`` reports a correctly-installed hook as missing — the same
    mistake ``init.sh`` made when *writing* the shim, so it would have told an
    adopter to re-run an install that had already worked.

    Read via a plain config-file scan rather than shelling out to ``git``, so
    this stays import- and subprocess-free.

    **Known-incomplete, deliberately (issue #61).** What this scan misses:

    - a ``hooksPath`` set anywhere but ``.git/config`` — ``~/.gitconfig``,
      ``$XDG_CONFIG_HOME/git/config``, an ``[includeIf]`` include;
    - git's own value normalization: surrounding quotes, inline ``#``/``;``
      comments, and ``~`` expansion;
    - case. Git config keys are case-insensitive, so ``git config
      core.hookspath X`` writes ``hookspath =`` and the ``startswith`` below
      does not match it;

    and, in the other direction, it matches ``hooksPath`` under *any* section,
    plus any key merely beginning with those letters.

    Asking git instead is the obvious fix and was attempted; a review panel
    found that version answered from an *enclosing* repository when `root` was
    not one, and honored an inherited ``GIT_DIR`` — both silent, both worse than
    these false negatives. Reverted rather than shipped half-right; #61 carries
    the evidence and the shape a correct version needs.

    **Not fixed by that revert, and present here:** ``.git/hooks`` is appended
    unconditionally, so a hook sitting there reports as installed even when
    ``core.hooksPath`` sends git somewhere else and git will never run it. That
    is a false POSITIVE on a quality gate, it predates this file's current
    shape, and it is part of what #61 has to resolve.
    """
    candidates: list[Path] = []
    config = root / ".git" / "config"
    if config.is_file():
        for line in config.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("hooksPath"):
                _, _, value = stripped.partition("=")
                value = value.strip()
                if value:
                    path = Path(value)
                    candidates.append(path if path.is_absolute() else root / path)
    candidates.append(root / ".git" / "hooks")
    return [c / "pre-push" for c in candidates]


def _remap(rel: str, engines_dir: str) -> str:
    """Rewrite a kit-layout path onto the adopter's engines directory."""
    engines_dir = engines_dir.rstrip("/") or KIT_ENGINE_PREFIX
    if engines_dir == KIT_ENGINE_PREFIX:
        return rel
    if rel == KIT_ENGINE_PREFIX or rel.startswith(KIT_ENGINE_PREFIX + "/"):
        return engines_dir + rel[len(KIT_ENGINE_PREFIX) :]
    return rel


def generate_manifest(root: Path, kit_version: int) -> dict:
    """Hash every kit-owned file in the kit's own checkout.

    Run in the kit repo at release time. A file listed in ``KIT_OWNED`` but
    absent here is recorded as ``None`` rather than skipped, so a packaging
    mistake shows up as an explicit hole instead of silently narrowing what
    later gets checked.

    ``required_by`` is written only where the derived dependent set is non-empty
    — most kit files are needed by nothing, and an entry per file would be
    twenty-six empty lists to read past in every manifest diff (32 KIT_OWNED
    entries, 6 with a dependent; the earlier figure of "thirty" was a guess and
    the correctness lens on PR #225 computed the real one). A reader must
    therefore treat an ABSENT key as "no known dependents", which is also what
    an older manifest (written before this field existed) yields: it reports
    every missing file as an ordinary `missing`, exactly as it did before.
    Degrading to the previous behaviour is the intended failure mode.
    """
    dependents = derive_dependencies(root)
    files: dict[str, dict] = {}
    for rel, role in KIT_OWNED:
        target = root / rel
        files[rel] = {
            "sha256": sha256_of(target) if target.is_file() else None,
            "role": role,
        }
        if dependents.get(rel):
            files[rel]["required_by"] = dependents[rel]
    return {
        "kit_version": kit_version,
        "files": files,
        "adopter_owned": list(ADOPTER_OWNED),
    }


def inspect(root: Path, manifest: dict, config: dict) -> Report:
    engines_dir = str(get(config, "paths.engines", KIT_ENGINE_PREFIX))
    manifest_files = manifest.get("files") or {}

    # Presence of EVERY kit-owned file, resolved before the status loop: whether
    # a missing file is a broken install or a sized-down one is a question about
    # its dependents, and those can sit anywhere in KIT_OWNED order.
    present = {rel: (root / _remap(rel, engines_dir)).is_file() for rel, _ in KIT_OWNED}

    statuses: list[FileStatus] = []
    for rel, role in KIT_OWNED:
        local_rel = _remap(rel, engines_dir)
        target = root / local_rel
        entry = manifest_files.get(rel) or {}
        expected = entry.get("sha256")
        if not target.is_file():
            # Filtered to INSTALLED dependents. A repo that installed no engine
            # is a supported sized-down adoption and must not be told its
            # missing library breaks it — the same distinction `_ENGINE_NAMES`
            # exists to keep the engines probe from getting wrong (#59).
            needed_by = [dep for dep in (entry.get("required_by") or []) if present.get(dep)]
            if needed_by:
                names = ", ".join(PurePosixPath(dep).name for dep in needed_by)
                statuses.append(
                    FileStatus(local_rel, role, "missing-required", f"needed by {names}")
                )
            else:
                statuses.append(FileStatus(local_rel, role, "missing"))
            continue
        if expected is None:
            statuses.append(FileStatus(local_rel, role, "unknown-version", "no manifest entry"))
            continue
        actual = sha256_of(target)
        if actual == expected:
            statuses.append(FileStatus(local_rel, role, "unchanged"))
        else:
            statuses.append(
                FileStatus(local_rel, role, "differs", f"{actual[:12]} != {expected[:12]}")
            )

    # A configured engines dir that holds no engine is the silent failure that
    # made one surveyed repo's workflows resolve `<engine-dir>/…` to nothing.
    # ANY kit engine counts (see `_ENGINE_NAMES`): a sized-down adoption is a
    # supported state, so the probe must answer "is this the engines dir?" and
    # not "did you install the three I happen to name?".
    engines_probe = any((root / engines_dir / name).is_file() for name in _ENGINE_NAMES)

    hook_target = root / engines_dir / "hooks" / "pre-push"
    hooks_installed = hook_target.is_file() and any(
        candidate.is_file() for candidate in _hook_dirs(root)
    )

    narrative: dict[str, bool] = {}
    for key in ("paths.handoff", "paths.friction_log"):
        rel = get(config, key, None)
        if not rel:
            continue
        doc = root / str(rel)
        # "Rendered" = present and no longer carrying the shipped marker ON LINE 1.
        # This mirrors init.sh's seed guard, which reads only the first line:
        # matching anywhere made the two disagree about the same file — a doc that
        # merely quotes the marker in prose was reported "still an unrendered
        # template — run ./init.sh" while init.sh correctly left it alone, making
        # the prescribed remedy a no-op (panel round 2).
        #
        # read_BYTES, not read_text: read_text() applies universal-newline
        # translation, so a lone CR ends its "first line" while `head -n 1` ends
        # only at LF. Round 2's fix used read_text and so swapped one divergence
        # for another — on a CR-delimited file the doctor said "in use" while
        # init.sh seeded over it (panel round 3). Splitting the raw decode on "\n"
        # is what head -n 1 actually does.
        #
        # Known remaining divergence, pre-existing and unrelated to line
        # matching: an unreadable file makes init.sh's guard fail safe ("in
        # use") while this raises PermissionError and aborts the whole run.
        # Not filed as of this change, and deliberately not fixed here — note
        # that pr_watch and pr_followup_hook both treat an unreadable config as
        # "must never raise", so this check is the outlier.
        narrative[str(rel)] = doc.is_file() and (
            "devkit-template: unrendered"
            not in doc.read_bytes().decode("utf-8", "replace").split("\n", 1)[0]
        )

    raw_version = get(config, "kit.version", None)
    raw_manifest_version = manifest.get("kit_version")
    return Report(
        kit_version_config=_as_version(raw_version),
        kit_version_manifest=_as_version(raw_manifest_version),
        kit_version_config_raw=raw_version,
        kit_version_manifest_raw=raw_manifest_version,
        engines_dir=engines_dir,
        engines_dir_ok=engines_probe,
        hooks_installed=hooks_installed,
        narrative_rendered=narrative,
        files=statuses,
    )


def render(report: Report) -> str:
    lines: list[str] = ["kit-doctor — installation report", ""]
    cfg_v, man_v = report.kit_version_config, report.kit_version_manifest
    if cfg_v is None and report.kit_version_config_raw is not None:
        # Present but not a number. Deliberately NOT the "run ./init.sh to
        # migrate" advice below: the fix is a one-character config edit, and
        # sending someone into a migration for a typo is the same wrong-advice
        # failure as the engines probe in #59.
        lines.append(
            f"  ⚠ config schema: UNREADABLE — kit.version is {report.kit_version_config_raw!r}, "
            "expected an unquoted or quoted integer (e.g. `version: 2`)"
        )
    elif cfg_v is None:
        lines.append("  ⚠ config schema: UNVERSIONED (pre-v2) — run ./init.sh to migrate and stamp")
    elif man_v is not None and cfg_v < man_v:
        lines.append(f"  ⚠ config schema: v{cfg_v}, kit ships v{man_v} — run ./init.sh to migrate")
    else:
        lines.append(f"  ✓ config schema: v{cfg_v}")

    # The manifest's version gets its OWN line rather than an `elif` above, for
    # two reasons the previous shape got wrong: an ABSENT or null kit_version
    # leaves the comparison just as impossible as an unreadable one (and used to
    # fall through to a bare ✓), and a config-side problem used to swallow the
    # manifest-side one entirely, so a packaging fault went unnamed.
    if man_v is None:
        raw = report.kit_version_manifest_raw
        detail = "absent" if raw is None else repr(raw)
        lines.append(
            f"  ⚠ manifest kit_version is {detail} — cannot tell whether this config is "
            "behind the kit"
        )

    if report.engines_dir_ok:
        lines.append(f"  ✓ paths.engines: {report.engines_dir}")
    else:
        lines.append(
            f"  ✗ paths.engines: {report.engines_dir} — contains no kit engine. "
            "Every workflow's <engine-dir>/… reference resolves to nothing."
        )

    lines.append(
        f"  {'✓' if report.hooks_installed else '⚠'} pre-push hook: "
        + ("installed" if report.hooks_installed else "NOT installed — run ./init.sh")
    )
    for doc, rendered in report.narrative_rendered.items():
        lines.append(
            f"  {'✓' if rendered else '⚠'} {doc}: "
            + ("in use" if rendered else "still an unrendered template — run ./init.sh")
        )

    by_state: dict[str, list[FileStatus]] = {}
    for f in report.files:
        by_state.setdefault(f.state, []).append(f)

    # `missing` counts BOTH absent states, so the total does not change meaning
    # for anyone reading this line as "how much of the kit is not here"; the
    # parenthetical is what says how much of that absence is breakage. Rendered
    # only when non-zero, so a healthy install's summary line is unchanged.
    n_required_missing = len(by_state.get("missing-required", []))
    n_absent = len(by_state.get("missing", [])) + n_required_missing
    absent_note = (
        f" ({n_required_missing} required by an installed engine)" if n_required_missing else ""
    )
    lines.append("")
    lines.append(
        f"  files: {len(by_state.get('unchanged', []))} unchanged, "
        f"{len(by_state.get('differs', []))} differ, "
        f"{n_absent} missing{absent_note}, "
        f"{len(by_state.get('unknown-version', []))} unknown"
    )
    # Narrow "differs" using the schema version rather than asserting a cause.
    # An UNREADABLE version narrows nothing: "no version key" soundly implies
    # pre-v2 and therefore older, but `version: v2` implies nothing at all, and
    # this file's whole position on `differs` is that it must not claim a cause
    # it cannot know.
    config_unreadable = (
        report.kit_version_config is None and report.kit_version_config_raw is not None
    )
    # A manifest with no USABLE version — absent, null, or unparseable — is no
    # comparison point at all. Only qualified by a versioned config, because an
    # UNVERSIONED config is pre-v2 by definition and therefore older regardless.
    cannot_narrow = config_unreadable or (
        report.kit_version_manifest is None and report.kit_version_config is not None
    )
    # `behind` has THREE consumers: the `elif` below, the `else` below, and the
    # kit-bug nudge after this block. It is deliberately not re-qualified by
    # `cannot_narrow` — each consumer handles that itself, and a redundant
    # condition here would pin nothing while reading as if it did.
    behind = (
        report.kit_version_config is not None
        and report.kit_version_manifest is not None
        and report.kit_version_config < report.kit_version_manifest
    ) or (report.kit_version_config is None and not config_unreadable)
    if cannot_narrow:
        differs_label = (
            "differ from the manifest — a schema version is unusable, so it "
            "cannot narrow this to an older kit versus local edits; diff before replacing"
        )
    elif behind:
        differs_label = (
            "differ from the manifest — this repo's config predates the kit's, so these are "
            "probably just an OLDER version rather than local edits; diff to confirm"
        )
    else:
        differs_label = (
            "differ from the manifest — same schema version, so these are likely LOCAL EDITS; "
            "diff before replacing"
        )
    for state, label in (
        # First, and phrased to leave no room for the "deliberate omission"
        # reading: this is the one absent-file case where the answer is not
        # "decide, don't assume" but "install it".
        (
            "missing-required",
            "✗ NOT INSTALLED, and needed by an engine that is — this install is "
            "broken, not sized down. Install these before refreshing any engine",
        ),
        ("differs", differs_label),
        ("unknown-version", "no manifest entry — drift cannot be judged"),
        ("missing", "not installed (sized-down adoption, or incomplete)"),
    ):
        items = by_state.get(state) or []
        if not items:
            continue
        lines.append(f"\n  {label}:")
        for f in items:
            suffix = f"  ({f.detail})" if f.detail else ""
            lines.append(f"    · {f.path} [{f.role}]{suffix}")

    # `not cannot_narrow` is load-bearing, and only for the MANIFEST side: an
    # unreadable *config* version leaves `behind` True and is suppressed by that
    # alone, but an unusable *manifest* version leaves `behind` False, so
    # without this the nudge would fire on a comparison that never ran — telling
    # the adopter to report a kit bug on the strength of nothing.
    if by_state.get("differs") and not behind and not cannot_narrow:
        lines.append(
            "\n  Engines are kit-owned: everything project-specific belongs in"
            "\n  config/dev-model.yaml. If you had to edit an engine to adopt it,"
            "\n  that is a kit bug — please report it rather than carrying the patch."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report kit installation drift.")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--generate-manifest",
        action="store_true",
        help="(kit repo only) hash every kit-owned file and write kit-manifest.json",
    )
    parser.add_argument("--root", type=Path, default=None, help="repo root (default: discovered)")
    parser.add_argument("--manifest", type=Path, default=None, help="path to kit-manifest.json")
    args = parser.parse_args(argv)

    root = (args.root or repo_root()).resolve()
    manifest_path = args.manifest or (root / MANIFEST_NAME)

    try:
        config = load_config(root / "config" / "dev-model.yaml")
    except ValueError as exc:
        # A local config overlay that cannot be applied. Sibling engines already
        # catch ValueError here; this one caught only FileNotFoundError and so
        # tracebacked on it, against the repo's own convention that a config error
        # reports cleanly (panel, adversarial lens).
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "hint: a repo with no config/dev-model.yaml predates the config surface "
            "entirely — adopt it with the /adopt skill rather than upgrading.",
            file=sys.stderr,
        )
        return 2

    if args.generate_manifest:
        # An absent (or explicitly null) kit.version takes the documented
        # default; only a value that is PRESENT and unreadable is refused. The
        # earlier shape defaulted before parsing, so it printed "kit.version is
        # None" for a null key while silently stamping 2 for an absent one —
        # naming the one case that did not error.
        raw_version = get(config, "kit.version", None)
        version = 2 if raw_version is None else _as_version(raw_version)
        if version is None:
            # Refuse rather than guess: a manifest stamped with the wrong
            # kit_version misreports drift for every adopter that reads it.
            print(
                f"error: kit.version is {raw_version!r}, expected an unquoted or quoted "
                "integer — refusing to stamp a manifest with a guessed version",
                file=sys.stderr,
            )
            return 2
        manifest = generate_manifest(root, version)
        # Truncating write, deliberately: #174 carries the decision, the
        # measurements and the objections. Not restated here — every review round
        # so far has found a defect in some version of the argument kept at this
        # site, and an argument that long belongs on the issue.
        #
        # The one local fact: this call is unwrapped and the "wrote ..." line below
        # follows it, so a failure here makes **no claim about damage**. #164's
        # defect was making a FALSE one — it exited 2 saying "no changes applied"
        # over a destroyed document. Recovery is a re-run, plus `git checkout` for
        # a manifest git TRACKS. Tracked is the property that makes that work, not
        # location: `--manifest` and `--root` can both aim at an untracked path,
        # inside the repo or outside it.
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        holes = [p for p, e in manifest["files"].items() if e["sha256"] is None]
        print(f"wrote {manifest_path} ({len(manifest['files'])} files, kit_version={version})")
        if holes:
            print(
                f"warning: {len(holes)} listed file(s) absent from this checkout:", file=sys.stderr
            )
            for h in holes:
                print(f"  · {h}", file=sys.stderr)
        return 0

    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        print(
            "hint: copy kit-manifest.json in from the kit release you are comparing against.",
            file=sys.stderr,
        )
        return 2
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"error: unreadable manifest {manifest_path}: {exc}", file=sys.stderr)
        return 2

    report = inspect(root, manifest, config)

    if args.json:
        print(
            json.dumps(
                {
                    "kit_version_config": report.kit_version_config,
                    "kit_version_manifest": report.kit_version_manifest,
                    # A null parsed value with a non-null raw one means the key
                    # is present but unreadable, which a consumer cannot
                    # otherwise distinguish from an absent version.
                    "kit_version_config_raw": report.kit_version_config_raw,
                    "kit_version_manifest_raw": report.kit_version_manifest_raw,
                    "engines_dir": report.engines_dir,
                    "engines_dir_ok": report.engines_dir_ok,
                    "hooks_installed": report.hooks_installed,
                    "narrative_rendered": report.narrative_rendered,
                    "files": [
                        {"path": f.path, "role": f.role, "state": f.state, "detail": f.detail}
                        for f in report.files
                    ],
                },
                indent=1,
            )
        )
    else:
        print(render(report))

    if report.kit_version_config is None and report.kit_version_config_raw is not None:
        # Unreadable input, per the exit-code contract above. Reported first so
        # the adopter sees the ⚠ line, then a non-zero status so CI cannot go
        # green on a config this very run called UNREADABLE.
        return 2
    return 1 if report.drifted or report.broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
