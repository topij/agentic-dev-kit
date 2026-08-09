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
    so rather than guessing. Reachable only WITHOUT a declared install set —
    with one, every absence resolves to `declined`, `removed` or `new-upstream`
    below, and this state does not occur.
``declined``
    Not installed, and the baseline records that it was already absent when the
    install was recorded — a deliberate omission. Not a finding: a sized-down
    adoption is a supported state, so this is what "intact for this adoption"
    is counted from.
``removed``
    Not installed, but the baseline records it AS installed. Something deleted
    it after the install was recorded. This is the failure `missing` could not
    report (issue #286): under one undifferentiated count, deleting four
    engines moved the number and said nothing, because the healthy state was
    reported in the same words.
``new-upstream``
    Not installed, and the baseline mentions it in NEITHER map. The ordinary
    cause is that the kit gained it after this repo's baseline was recorded, so
    no declared set could have mentioned it. Informational, never a finding: it
    is neither broken nor declined, it has simply never been offered.
    `/upgrade` is where it gets accepted or declined.

    **This state is where a damaged baseline shows up, and it cannot tell the
    two apart.** Deleting one key from ``files`` turns a ``removed`` finding
    (exit 1) into this line (exit 0) for a file that WAS installed and then
    deleted — the same absence-from-both-maps shape, reached by corruption
    instead of by a kit release. Nothing here can separate them: the baseline is
    the trust root, ``_baseline_trusted`` keys on the PRESENCE of ``kit_commit``
    rather than on integrity, and a record that lies about itself defeats every
    conclusion drawn from it. So the report states what it knows — the baseline
    does not mention these — and names the likely cause as likely. Making the
    distinction mechanical needs an integrity-protected baseline, which is a
    larger change than this axis.
``missing-required``
    Not installed, but an engine that IS installed needs it — so this install
    is broken, not sized down. The distinction exists because the old report had
    only ``missing``, which files a hard dependency under "sized-down adoption,
    or incomplete" alongside `docs/templates/*.tmpl`, which genuinely are
    optional. `/upgrade` then tells the operator that a missing piece may be a
    deliberate omission and to ask before installing it — so the documented path
    invited someone to decline `lib/kitconfig.py`, which every Python engine
    imports (issue #41). Which files these are is DERIVED at
    ``--generate-manifest`` time from the PYTHON import graph, not restated by
    hand. Shell ``source`` is deliberately NOT scanned — see
    `derive_dependencies` for the gap that leaves and why it is left open.
``stale``
    Byte-identical to what THIS repo installed (per its baseline — see
    ``--record-install``), and different from what the kit ships. Nothing was
    edited here; replace it. Only reachable with a trusted baseline.
``locally-edited``
    Changed here since install, while the kit's copy did not move. Reconcile
    the edit into ``config/dev-model.yaml``, then take the kit's copy. Only
    reachable with a trusted baseline.
``stale-and-edited``
    Changed on both sides. The only state that can lose work, so it is named
    separately rather than folded into either single-sided one. Only reachable
    with a trusted baseline.
``unknown-version``
    The manifest has no entry for this file, so drift can't be judged.

The three states above are refinements of ``differs``, not lesser categories:
they all count as drift, and all of them exit 1. Without a trusted baseline —
one carrying ``kit_commit``, which only ``--record-install`` writes — every
mismatch stays ``differs`` and no cause is claimed.

**The declared install set** works the same way one axis over, and is what
splits ``missing`` into the three states above it. ``--record-install`` writes
``not_installed``: the kit-owned paths that were absent at record time, which
it already walks and until #286 simply dropped. An absence is then judged
against the record rather than guessed at — declared out of scope, deleted
since install, or newer than the baseline.

Two properties of that split are deliberate and load-bearing:

- **It is derived, never declared by hand.** ``--record-install`` knows exactly
  which paths were absent when it ran; an operator-maintained list in the
  config would be a second copy of that fact, and the copy is what goes stale.
- **A baseline without the key gets the OLD behaviour, not a guessed one.**
  Every baseline recorded before #286 predates ``not_installed``, and inferring
  "declined" from its silence would assert an intent nobody expressed — and
  would quietly absorb ``new-upstream`` into it, since a file the kit added
  later is absent from a pre-#286 baseline in exactly the same way. So the key
  must be PRESENT to enable the split; its absence keeps plain ``missing`` and
  the report says why, with the one command that fixes it.

Adopter-owned paths (the config, the narrative docs) are **never** compared —
they are supposed to differ, and reporting them as drift would bury the signal.

`paths.engines` indirection is handled: the manifest records the kit's own
layout (``scripts/…``), and comparison maps that prefix onto whatever the
adopter configured, so a repo that vendored engines under ``scripts/devkit/``
compares correctly without a rewritten manifest.

Read-only when REPORTING. Two flags write, and each writes exactly one file:
``--generate-manifest`` produces the kit's release manifest and is for the kit's
own checkout; ``--record-install`` produces an adopter's install baseline and is
for an adopter. They are not interchangeable, and the second refuses to
overwrite anything it did not write itself — see ``_was_written_by_record_install``
for the signal and ``main``'s ``--record-install`` branch for the refusal.

Usage (``<engine-dir>`` is ``paths.engines`` in config/dev-model.yaml, default
``scripts`` — every workflow doc writes it the same way; see
``docs/agentic-dev-kit/workflows/*.md``):
    uv run <engine-dir>/kit_doctor.py                    # human report
    uv run <engine-dir>/kit_doctor.py --json             # machine-readable
    uv run <engine-dir>/kit_doctor.py --generate-manifest  # (kit repo) refresh the manifest
    uv run <engine-dir>/kit_doctor.py --record-install --from-kit <kit checkout>
                                                    # (adopter) record the install baseline
    uv run <engine-dir>/kit_doctor.py --manifest <kit checkout>/kit-manifest.json
                                                    # compare against upstream, splitting
                                                    # drift by cause

Exit codes:
    0 — every kit-owned file is `unchanged`, or absent without being a finding:
        `declined` (intentionally absent), `missing` (absent, intent unknown),
        or `new-upstream`. The last is deliberately in this list and is NOT
        "intentionally absent" — nobody has been asked about it yet — which is
        why this line no longer says that of every absence. It exits 0 because
        a kit release must not turn an adopter's CI red.
    1 — at least one file `differs`, is `stale`, `locally-edited`,
        `stale-and-edited`, `unknown-version`, `missing-required`, or
        `removed`. The last two are not drift, but they are a broken
        install, and the exit code an adopter gates CI on should not be green
        for a tree whose engines cannot load their own library. `declined` and
        `new-upstream` are NOT in this set and never fail the gate: the first
        is the supported sized-down state, and the second is a file the adopter
        has never been asked about — failing CI on either would make the gate
        fire on a healthy repo and on every kit release respectively.
        Under ``--record-install`` this same code means the baseline was
        written but some present kit-owned path was EXCLUDED from it — see that
        mode's stderr list. Exiting 0 there would let a caller that reads only
        the status code treat a partial record as a complete one.
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
import re
import subprocess
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
    # `/adopt` and `/upgrade`. These were `.claude/commands/` adapters until #330, and
    # tracking them is the POINT of that move rather than a consequence of it: Step 4 of
    # upgrade.md tells an upgrading adopter to "keep the adopter's version where one
    # already exists" for runtime adapters, so for as long as these two lived only there,
    # every kit fix to the adopt and upgrade procedures was unreachable by the adopters
    # running them — including the #297 hazard fix that #330 is about. A workflow whose
    # own upgrade path cannot upgrade it is the closed loop being broken here.
    ("docs/agentic-dev-kit/workflows/adopt.md", "workflow"),
    ("docs/agentic-dev-kit/workflows/upgrade.md", "workflow"),
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
    # The two runtime entry points render from these (#92). Only the TEMPLATES
    # are kit-owned: the rendered root AGENTS.md and CLAUDE.md are the adopter's
    # to extend, so both are listed in ADOPTER_OWNED below instead.
    ("docs/templates/AGENTS.md.tmpl", "template"),
    ("docs/templates/CLAUDE.md.tmpl", "template"),
    # The installer itself (#360). Untracked until now, which made it the one
    # file this report structurally could not range over — while being the file
    # that PERFORMS every install and upgrade. cs-toolkit's copy measured 852
    # differing lines against kit `3761bec` — and the COMMAND matters, because the
    # count is argument-order dependent and two review lenses reached opposite
    # verdicts on this number without it:
    #
    #     diff <adopter>/init.sh <kit>/init.sh | grep -c '^[<>]'   # 852
    #     diff <kit>/init.sh <adopter>/init.sh | grep -c '^[<>]'   # 848
    #
    # Adopter first, as `#360` wrote it. Neither figure is wrong; `diff` simply
    # picks a different edit script per direction on a file with many similar
    # lines. Both re-measured here 2026-08-08. Below, "852" always means the
    # first form.
    #
    # While that drift stood, cs-toolkit's doctor said `13 unchanged, 0 differ,
    # 0 missing` and exited 0. Every statement in that report was true; the drift
    # was entirely outside what it ranged over.
    #
    # `#360` framed the tracking model as a three-way design choice, on the
    # premise that an adopter's copy is EXPECTED to diverge because it "encodes
    # answers to the adoption prompts" — which would make a plain entry here
    # report every adopter permanently `locally-edited`, re-creating the
    # permanently-red failure `#286` was closed to fix. THAT PREMISE IS FALSE,
    # and the choice dissolves with it:
    #
    #   - cs-toolkit's init.sh is BYTE-IDENTICAL to kit commit `7485512b`
    #     (2026-07-26) — established by hashing its copy and scanning every
    #     init.sh blob in this repo's history for a match. So all 852 lines are
    #     version drift and NONE are local rendering.
    #   - init.sh never writes to itself. It writes config/dev-model.yaml and
    #     renders docs/templates/. Pinned BEHAVIOURALLY by
    #     `test_init_sh.py::test_running_the_installer_does_not_modify_the_installer`
    #     IN THE KIT REPO — `KIT_OWNED` tracks no tests, so that suite does not
    #     travel to an adopter and this is not a guarantee where you are reading
    #     it if you are reading it downstream (#386) —
    #     which runs the installer and compares its own bytes. (This line used to
    #     name `test_the_installer_is_not_self_modifying`, a regex over init.sh's
    #     source that the commit adding this entry deleted — two review lenses
    #     defeated it with an indirect self-write. A correctness lens then caught
    #     the reference still pointing at the deleted name.)
    #   - Nothing in the kit tells an adopter to edit it.
    #
    # So `_drift_state` puts an unedited, behind-the-kit copy in `stale`
    # ("installed X, kit ships Y") — true, actionable, and it clears to
    # `unchanged` when the adopter updates the file. Not permanent, and not
    # `locally-edited`. No new role that exempts it, and no split into tracked
    # engine + rendered part; both were candidates in the issue and both are
    # answers to a problem that does not exist.
    #
    # Role `installer` rather than `engine`, for mechanical reasons, not taxonomy.
    # Stated precisely, because an earlier version of this comment overstated the
    # first one and an adversarial lens measured it:
    #
    #   - `_derive_engine_names` requires role `engine` AND the `scripts/` prefix.
    #     init.sh's path has no such prefix, so role alone would NOT put it in
    #     `_ENGINE_NAMES` — the function applies both filters BEFORE slicing, so
    #     it simply skips the entry and no empty probe name is ever produced.
    #     (This bullet used to say the empty string is what role `engine` makes
    #     the FUNCTION produce. It is not; CodeRabbit caught that, reviewing an
    #     adopter's PR where this file appeared in the diff — #383 item 2.)
    #
    #     Where the empty string actually arises is
    #     `test_engine_probe_names_cover_the_real_kit_owned_engines` IN THE KIT
    #     REPO, which slices every `engine`-role entry unconditionally and
    #     asserts the result is in `_ENGINE_NAMES` — so `""` fails it. The guard
    #     is therefore real and pre-existing, and it is a TEST rather than an
    #     invariant in this module. Re-measured 2026-08-09 rather than restated:
    #     with `("init.sh", "engine")` substituted in a scratch copy, three tests
    #     fail — `test_the_installer_is_tracked`,
    #     `test_an_unedited_installer_behind_the_kit_reports_stale_not_locally_edited`,
    #     and that one, at its slice assertion. `KIT_OWNED` ships no tests, so an
    #     adopter reading this comment has none of them (#386).
    #   - The `_TEXT_IMPORT_RE` dependency scan applies to `engine` and `hook`
    #     only. init.sh declares no non-stdlib dependency, so scanning it would
    #     manufacture edges out of a shell script's own prose.
    #
    # And the reason it is not an engine at all: it does not move with
    # `paths.engines`. It sits at the repo root by definition, being what an
    # adopter runs *before* a configured path exists.
    #
    # MIGRATION, and it is not a defect: an adopter whose recorded baseline
    # predates this entry has init.sh PRESENT locally and ABSENT from that
    # baseline, which `_drift_state` reports as `differs` ("not in baseline")
    # rather than `new-upstream` — the latter only covers files that are absent.
    # That exits 1 until they re-record with `--record-install`. Correct: their
    # installer really is unmeasured, and that is the whole finding.
    ("init.sh", "installer"),
)

# The kit-layout key for the pre-push hook, derived from KIT_OWNED rather than
# spelled again: `not_installed` records these keys, so a declined-hook check
# comparing against a hand-written literal would silently stop matching the day
# the path moves — and the failure would be a decline reported as a defect,
# which is the very thing #381 is about. Empty when no such entry exists, which
# simply means no decline can be recognised.
PRE_PUSH_REL = next(
    (rel for rel, role in KIT_OWNED if role == "hook" and PurePosixPath(rel).name == "pre-push"),
    "",
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
    # Rendered from the templates above; unlike an engine both are meant to be
    # edited, so neither may ever be reported as drift. CLAUDE.md joins the list
    # because the kit now ships its own copy of each — before that it shipped
    # neither, and a `cp -r` adopter kept the KIT's CLAUDE.md as their contract
    # with nothing rendering over it and nothing reporting it.
    "AGENTS.md",
    "CLAUDE.md",
    # This repo's own narrative files (see the note in config/dev-model.yaml).
    "docs/kit-handoff.md",
    "docs/kit-handoff-history.md",
    "docs/kit-friction-log.md",
    "docs/kit-friction-log-archive.md",
    "README.md",
    ".gitignore",
)

# The two line-1 markers `init.sh` seeds by, and the rule for reading one. This
# MUST agree with `init.sh`'s `_seedable`, because the two answer the same
# question about the same file and a disagreement makes the doctor prescribe a
# remedy `init.sh` then refuses to perform.
#
# It has diverged twice. Round 2 anchored `init.sh` to line 1 and this to the
# whole file; round 6 anchored `init.sh` to the opening HTML comment and left
# this a bare substring, so a doc whose line-1 comment merely MENTIONS a marker
# was reported "still an unrendered template — run ./init.sh" while `init.sh`
# correctly left it alone.
SEED_MARKERS: tuple[str, ...] = ("devkit-template: unrendered", "devkit-source: kit-own")

# `[[:space:]]` in the C locale. That class is LOCALE-DEPENDENT in the shell, so
# `init.sh` pins `LC_ALL=C` at both places it uses one — without that, a UTF-8
# locale made the shell match NBSP and U+2028 where this does not, and the two
# predicates disagreed about a file `init.sh` would overwrite (panel round 7).
# If that pin is ever removed, this set stops describing the other side.
POSIX_BLANKS = " \t\n\v\f\r"


def _still_a_skeleton(first_line: str) -> bool:
    """True when line 1 opens an HTML comment whose first token is a seed marker.

    `<!--`, optional blanks, the marker, then a blank or the end. Prose that
    merely mentions a marker does not qualify, and neither does
    `devkit-source: kit-ownership` — the boundary is what stops a prefix match.

    **This MUST agree with `init.sh`'s `_seedable` on every input**, and they are
    two independent implementations in two languages held together by this
    sentence and by matched test shapes — not by shared code. They have diverged
    three times; see SEED_MARKERS for the account. A disagreement is never
    cosmetic: the doctor then prescribes `run ./init.sh` for a file `init.sh`
    will refuse to touch, or stays silent about one it will overwrite.
    """
    if not first_line.startswith("<!--"):
        return False
    # POSIX_BLANKS, not " \t": `sed`'s `[[:space:]]` and the shell's
    # `[[:space:]]` glob both include CR, and `head -n 1` ends at LF only — so on
    # a CR-delimited file a marker comment can be followed by CR where this saw a
    # non-blank and disagreed with init.sh. Python's `str.isspace()` would also
    # accept Unicode spaces the C locale does not; the explicit set keeps the two
    # predicates reading the same characters.
    rest = first_line[len("<!--") :].lstrip(POSIX_BLANKS)
    for marker in SEED_MARKERS:
        if rest == marker:
            return True
        if rest.startswith(marker) and rest[len(marker)] in POSIX_BLANKS:
            return True
    return False


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
    would make the probe stat a path no layout produces. This paragraph used to
    end "Nothing in KIT_OWNED is outside the prefix today", which was already
    false when written — the workflow, doctrine and template entries are all
    outside it, and ``init.sh`` (#360) is one more. The skip is therefore load
    bearing right now rather than prophylactic, which is the opposite of what
    that sentence implied. What keeps it safe is the ``role == "engine"``
    conjunct: every path outside the prefix also carries a non-engine role, so
    the two filters agree today. Adding an ``engine``-role entry outside the
    prefix is the case that would produce a garbage probe path, and nothing
    stops it — see ``test_engine_probe_names_cover_the_real_kit_owned_engines``
    (in the KIT repo: ``KIT_OWNED`` tracks no tests, so an adopter has neither
    that test nor any other behavioural cover for this module — #386), which is
    what caught an attempt to give ``init.sh`` role ``engine``.

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

    **Shell `source` is NOT scanned, and this is the one real gap.**
    `dev_session.sh` and `reconcile_sessions.sh` both
    `source "$SCRIPT_DIR/lib/repo_root.sh"` — a hard dependency expressed as a
    path rather than a module — so a tree missing `lib/repo_root.sh` reports it
    as an ordinary `missing` while `bash scripts/dev_session.sh` dies on its
    `source` line. That is a live instance of #41's own bug class and it is
    knowingly left open; #228 carries it.

    A scanner for it was built across three review rounds and withdrawn. The
    short version: preventing FALSE edges requires recognising every real
    heredoc opener, and preventing MISSED edges requires knowing whether a
    `source` is in command position — both are tokenizer problems, and each
    regex approximation leaked in one direction or the other. A false edge is
    the harmful direction (it tells an adopter their working install is broken),
    and shipping a mechanism that can produce them is worse than shipping the
    Python-only graph plus a documented hole. #228 has the full account,
    including the four constructs that defeated the last version.

    Non-Python files ARE still scanned for Python-style imports: `pre-push` is
    bash, and its `from kitconfig import …` lives inside a `python3 - <<'PY'`
    heredoc that genuinely executes.

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
    - Shell `source` is not scanned at all, so `lib/repo_root.sh`'s two
      dependents are absent from the graph. Stated above; #228 carries it.
    - Every one of these bounds errs toward NO edge. That direction is chosen,
      not incidental: a missing edge degrades a file to plain `missing`, which
      is the pre-#41 behaviour and merely unhelpful, while a false edge tells an
      adopter their working install is broken and to install something they do
      not need. `missing-required` firing wrongly is worse than it not firing,
      and that asymmetry is what decided the shell-scan question above.
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
    return {path: sorted(deps) for path, deps in sorted(dependents.items())}


@dataclass
class FileStatus:
    path: str
    role: str
    state: str
    detail: str = ""


@dataclass
class RegistrationStatus:
    """One hook registration, judged by whether the path it names RESOLVES.

    Not by hash, and the distinction is the whole design (#379). `.claude/
    settings.json` and `.codex/hooks.json` are the adopter's files — `init.sh`
    prints both blocks and writes neither, precisely because their content is
    theirs (#303) — so hashing them would report every adopter permanently
    `locally-edited`, which is #286's failure. What the kit may legitimately
    assert is narrower and mechanical: a registration that names a path is
    claiming that path runs, and whether the file is there is checkable without
    any opinion about the rest of the file.

    That is the check that would have caught #359 and #368, both of which an
    operator experienced as *a hook that silently stopped firing* — a
    `PostToolUse` failure does not halt a session, so nothing else reports it.
    """

    runtime: str
    surface: str
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
    # Whether a baseline was available AND written by a kit that maintains it
    # (see `_baseline_trusted`). False keeps every mismatch in the undifferentiated
    # `differs` state, which is the pre-#51 behaviour and the honest answer when
    # the record cannot be relied on.
    baseline_trusted: bool = False
    # The kit commit the baseline says this install came from. None is a real,
    # supported value — a retro-recorded baseline does not know its provenance —
    # and is why this must never be used as the trust signal.
    baseline_kit_commit: str | None = None
    # True when the baseline and the comparison manifest are the same source —
    # the bare `kit_doctor.py` invocation, where both default to
    # `<root>/kit-manifest.json`. Then "differs from the kit" and "differs from
    # what I installed" are the SAME comparison, so staleness is not merely
    # unobserved, it is unobservABLE: `stale` and `stale-and-edited` cannot
    # occur. Every mismatch is a local edit, which is correct — but the label's
    # claim about the kit's own copy is not, and `render` drops it (panel,
    # adversarial lens).
    baseline_is_comparison: bool = False
    # Whether this run could judge absences against a recorded install set
    # (#286). False is the pre-#286 report, and is what every baseline written
    # before `not_installed` existed still gets — see `_declared_scope` for why
    # that is not inferred.
    declared_scope_known: bool = False
    # Whether the kit's `pre-push` is installed, DECLINED, or simply absent
    # (#381). `hooks_installed` above stays a plain bool and keeps its meaning —
    # a `--json` consumer reading it must not have the answer change shape under
    # it — so the third state arrives beside it rather than inside it.
    hooks_state: str = "not-installed"
    registrations: list[RegistrationStatus] = field(default_factory=list)
    files: list[FileStatus] = field(default_factory=list)

    @property
    def drifted(self) -> list[FileStatus]:
        # The three split states MUST be listed here. They are refinements of
        # `differs`, not new lesser categories: leaving one out would drop it
        # from the exit code and from the CI manifest gate, so a real drift
        # would report clean the moment the split started naming it precisely.
        return [
            f
            for f in self.files
            if f.state
            in ("differs", "stale", "locally-edited", "stale-and-edited", "unknown-version")
        ]

    @property
    def missing(self) -> list[FileStatus]:
        return [f for f in self.files if f.state == "missing"]

    @property
    def declined(self) -> list[FileStatus]:
        """Absences this repo's baseline records as deliberate."""
        return [f for f in self.files if f.state == "declined"]

    @property
    def new_upstream(self) -> list[FileStatus]:
        """Kit-owned files added after this repo's baseline was recorded."""
        return [f for f in self.files if f.state == "new-upstream"]

    @property
    def broken(self) -> list[FileStatus]:
        """Files that are not installed and should be.

        Two states, one conclusion: `missing-required` is absent-and-depended-on
        (derived from the import graph), `removed` is absent-and-recorded-as-
        installed (derived from the baseline). Both mean the tree is broken
        rather than sized down, so both reach the exit code the same way — which
        is what this property is for.

        Deliberately NOT folded into `drifted`: a file that is absent has not
        drifted from anything, and this report's whole position is that it does
        not claim more than it knows. They meet only at the exit code.

        `declined` and `new-upstream` are deliberately absent from BOTH. Putting
        either here would reinstate #286's bug with the sign flipped — a healthy
        sized-down adoption failing its own CI gate.
        """
        return [f for f in self.files if f.state in ("missing-required", "removed")]

    @property
    def dead_registrations(self) -> list[RegistrationStatus]:
        """Registrations that cannot fire, by the two routes there are.

        `broken` — the file it names is not there. `unreadable` — the
        registration file itself does not parse, so EVERY registration in it is
        unmeasurable, and the runtime that must parse the same JSON is no better
        placed than this check was. Leaving that one out was the shape #379 was
        filed about, one level up: a `⚠` line and exit 0 over a file whose hooks
        nobody can account for (panel, correctness lens, delta round 2).

        The omissions are the point, and they are the other three: `unregistered`
        and `absent` describe an adopter who has not wired the hook, which is a
        supported state — `init.sh` only ever PRINTS the block (#303) — and
        failing them would be #286's bug in a third place, a healthy adoption
        failing its own gate forever. `unresolvable` is a registration this check
        could not evaluate; reporting that as broken would be claiming a
        measurement it did not make.
        """
        return [r for r in self.registrations if r.state in ("broken", "unreadable")]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


# The two files a runtime reads to learn that the kit's hook exists, plus the
# overlay Claude Code merges over the first. Literals, for the same reason
# `AGENTS.md` and `CLAUDE.md` are literals in `inspect`: they are the runtime's
# names, not the adopter's, and there is no config key that could hold them —
# a repo that renamed `.claude/settings.json` has no hook either way.
#
# The third element is whether a file with NOTHING TO SAY is worth a line —
# both when it is absent and when it is present but registers no kit hook. The
# overlay is optional by design, so neither says anything about the install; the
# other two are worth stating once, because "no registration here" and "a
# registration that does not work" look identical to an operator who never sees
# the hook fire. (The comment named only the absent case, which is half of what
# the flag gates — panel, correctness lens.)
REGISTRATION_SURFACES: tuple[tuple[str, str, bool], ...] = (
    ("claude", ".claude/settings.json", True),
    ("codex", ".codex/hooks.json", True),
    ("claude", ".claude/settings.local.json", False),
)

# Expansions for the repo-root stand-in each runtime's registration uses. Claude
# Code exports `CLAUDE_PROJECT_DIR`; Codex exposes no project-dir variable at
# all, so the block `init.sh` prints assigns `root=$(git rev-parse
# --show-toplevel)` and interpolates that — the inline form is here too, because
# an adopter who wrote the registration by hand may not have used the variable.
_ROOT_PLACEHOLDERS: tuple[str, ...] = (
    "$CLAUDE_PROJECT_DIR",
    "${CLAUDE_PROJECT_DIR}",
    "$(git rev-parse --show-toplevel 2>/dev/null)",
    "$(git rev-parse --show-toplevel)",
    "$root",
    "${root}",
)


# Deep enough for any registration a runtime documents (the deepest real shape
# is event -> matcher entry -> hooks list -> hook object, four levels), shallow
# enough that a degenerate document cannot exhaust the interpreter's stack. The
# walk below is the one place this module recurses over adopter-supplied data.
_MAX_REGISTRATION_DEPTH = 64


class _RegistrationTooDeep(Exception):
    """The walk hit `_MAX_REGISTRATION_DEPTH`.

    Raised rather than returned so the surface can be reported `unreadable`,
    which is what it is: a document this check declined to walk to the bottom
    was not measured, and returning the commands found above the cap would say
    "no kit hook registered" about a file that may well register one.

    It is also what makes the cap TESTABLE. The first version returned an empty
    list, and the test written for it passed with the cap removed — `json.loads`
    exhausts its own recursion budget first on a 10,000-deep document, so the
    walk was never reached and the property was named by a test and pinned by
    nothing (panel, adversarial lens, delta round).
    """


def _hook_commands(node: object, depth: int = 0, inside_hooks: bool = False) -> list[str]:
    """Every ``command`` string anywhere in a registration document.

    A recursive walk rather than a path lookup into `hooks.PostToolUse[…]`:
    the event names differ per runtime and grow over time (`SessionStart` is
    already a second one), and a lookup that knows only the events the kit ships
    today would silently stop seeing a registration the day one is added — which
    is precisely the class of blindness this check exists to remove.

    Scoped to a `hooks` subtree, at any depth, and that scoping is load-bearing:
    `.claude/settings.json` carries `command` strings that are not hooks at all —
    `statusLine.command` is one — and judging those reported a repo with NO kit
    hook registered as having a BROKEN one, exit 1, while suppressing the line
    that would have said "none registered" (panel, adversarial lens, PR #389).
    Keying on `hooks` rather than on the event names keeps the property that
    made the walk worth having.

    Depth-capped, because the recursion is over a file the adopter owns and the
    parse above it already promises to degrade rather than abort. A valid but
    degenerately nested document (10,000 levels of `[[[…]]]`) raised
    `RecursionError` straight out of `inspect()` — a traceback instead of the
    per-file `unreadable` this module states as its own rule two functions up
    (panel, adversarial lens, PR #389).
    """
    if depth > _MAX_REGISTRATION_DEPTH:
        if not inside_hooks:
            # Deep material OUTSIDE a hooks subtree is not this check's business,
            # so stop descending and say nothing. Counting it against the budget
            # made an unrelated blob elsewhere in `.claude/settings.json` report
            # the whole surface `unreadable` — exit 1, on an install whose hook
            # was sitting shallow and resolvable right beside it. A permanent
            # false warning is the shape #381 exists to remove (panel,
            # adversarial lens, round 8).
            return []
        raise _RegistrationTooDeep(
            f"nesting deeper than {_MAX_REGISTRATION_DEPTH} levels — not walked"
        )
    found: list[str] = []
    if isinstance(node, dict):
        command = node.get("command")
        if inside_hooks and isinstance(command, str):
            found.append(command)
        for key, value in node.items():
            found.extend(_hook_commands(value, depth + 1, inside_hooks or key == "hooks"))
    elif isinstance(node, list):
        for value in node:
            found.extend(_hook_commands(value, depth + 1, inside_hooks))
    return found




# A stand-in for the repo root that survives word-splitting. NOT the root
# itself: a root path containing a space — `~/My Project`, a
# `OneDrive - Company` sync folder, a home directory built from someone's full
# name — ended the word at that space, and the remainder, beginning with `/`,
# was read as an absolute path and reported `✗ NO SUCH FILE` with exit 1 for a
# hook that is present and would fire. The same substitution makes the inline
# `$(git rev-parse --show-toplevel)` form safe, which carries spaces of its own.
#
# `_script_words` is where the marking now happens, per segment, because
# quoting decides whether a placeholder expands at all — see its docstring.
# (This comment named `_script_token`, the delimiter walk two rounds of fixes
# ago, and described the mechanism that replaced it as the one it replaced; a
# lens caught it. Same class as the rest of this session.)
#
# NUL cannot appear in a path or in JSON text, so it cannot collide with
# anything an adopter wrote.
_ROOT_SENTINEL = "\x00devkit-root\x00"


def _mark_root(command: str) -> str:
    """`command` with each known repo-root stand-in replaced by `_ROOT_SENTINEL`.

    Bare `$NAME` forms are replaced only when what follows cannot be part of a
    shell identifier. A plain `str.replace` rewrote `$rootcause_dir` — an
    adopter's own variable — into `<root>cause_dir`, and then reported the real,
    present hook `broken` at a path no shell would ever build: a shell resolves
    the longest identifier, never `$root` plus a literal remainder (panel,
    adversarial lens). The `${…}` and `$(…)` forms are self-delimiting and are
    replaced literally.
    """
    for placeholder in _ROOT_PLACEHOLDERS:
        if placeholder.endswith("}") or placeholder.startswith("$("):
            command = command.replace(placeholder, _ROOT_SENTINEL)
        else:
            command = re.sub(
                re.escape(placeholder) + r"(?![A-Za-z0-9_])", _ROOT_SENTINEL, command
            )
    return command


def _script_words(command: str) -> tuple[bool, list[str]]:
    """The shell WORDS of a command, quoting resolved and root placeholders
    marked — one pass, because in a shell those two things are the same pass.

    A hand-rolled delimiter walk was here first, and it was not shell-aware in
    ways that each produced a confident falsehood about a healthy install: it
    treated a quote as a word boundary, so `"$root"/scripts/hooks/x.py` — quoting
    only the part that needs it, and identical to the fully-quoted form — was cut
    at the closing quote and the remainder read as an absolute path; and it
    stopped at any space, cutting `"/My Project/scripts/hooks/x.py"` in half.

    `shlex` is the shell's own lexer, and neither of its modes fits: `posix=True`
    discards the quoting this needs (see below), and `posix=False` ENDS a word at
    a closing quote, splitting exactly the shape the walk got wrong. So the scan
    is here, and it is small: split on unquoted whitespace, and mark placeholders
    only in segments the shell would expand.

    **Single quotes suppress expansion**, and that is the load-bearing half:
    `'$CLAUDE_PROJECT_DIR/hook.py'` is a literal path containing a `$`, a
    registration that can never fire. Marking the root there anyway reported that
    dead hook as `resolves`, exit 0 — the exact failure #379 exists to catch
    (panel, adversarial lens, PR #389).

    A backslash escapes the next character outside single quotes, so an escaped
    space keeps a word whole. An unterminated quote leaves its tail literal,
    which is the conservative reading of a line no shell would run.
    """
    words: list[str] = []
    parts: list[str] = []
    buf: list[str] = []
    state: str | None = None
    escaped = False

    def flush(expandable: bool) -> None:
        if buf:
            segment = "".join(buf)
            parts.append(_mark_root(segment) if expandable else segment)
            buf.clear()

    def end_word() -> None:
        flush(state != "'")
        if parts:
            words.append("".join(parts))
            parts.clear()

    for char in command:
        if escaped:
            # An escaped character is LITERAL, so it must not be marked: a shell
            # never expands `\$CLAUDE_PROJECT_DIR`, and marking it anyway
            # reported a registration that can only fail as `resolves` — a dead
            # hook with a clean bill of health, which is #379's own failure
            # (panel, adversarial lens, round 9). Flushing first keeps the
            # segment before it expandable.
            flush(True)
            parts.append(char)
            escaped = False
        elif state != "'" and char == "\\":
            escaped = True
        elif state is None and char == "#" and not buf and not parts:
            # A shell never runs what follows an unquoted `#` at a word start.
            # The scan did, so a name mentioned in an explanatory comment beside
            # a hook line was read as an invocation — reporting a phantom
            # registration, or a dead one, from a comment (panel, adversarial
            # lens, round 7).
            break
        elif state is None and char in " \t\n\r":
            end_word()
        elif state is None and char in "\"'":
            flush(True)
            state = char
        elif state == char:
            flush(state == '"')
            state = None
        else:
            buf.append(char)
    end_word()

    cleaned = []
    for word in words:
        if "=" in word:
            # An assignment form (`HOOK="$root/…"`) should yield the path.
            word = word.rsplit("=", 1)[-1]
        # A separator glued to the last word of a statement (`…/hook.py; exec …`).
        cleaned.append(word.rstrip(";&|"))
    # `state` is still set only when a quote never closed. A shell would refuse
    # the line too, so the honest report is that this command was not judged —
    # not that it registers nothing, and not that its path is missing.
    return state is None, cleaned


# What a file is renamed to when it is taken out of service, rather than "any
# single extra extension" — see `_match_word`.
_OUT_OF_ROTATION_SUFFIXES = frozenset(
    {"disabled", "off", "bak", "old", "orig", "unused", "save", "skip"}
)


def _match_word(words: list[str], name: str) -> str | None:
    """The word naming `name`, or None.

    Matched on the BASENAME rather than by substring: `env_paths.py` ends with
    `paths.py`, and matching that claimed an adopter's own file as the kit's.
    """
    for word in words:
        base = PurePosixPath(word).name
        if base == name:
            return word
        # A named out-of-rotation suffix, and nothing else. `hook.py.disabled` is
        # the kit's own hook taken out of service and worth reporting dead;
        # `logs/hook.py.log` is an unrelated ARGUMENT, and claiming it produced
        # `✗ NO SUCH FILE` and exit 1 for a repo that had registered no kit hook
        # at all. The rule was "one extra extension with no further dot", which
        # excluded `.out.log` and admitted `.log` — the commoner spelling of the
        # same thing (panel, adversarial lens, rounds 6 and 7).
        #
        # An allowlist errs toward silence: a hook renamed to something not
        # listed reports as unregistered rather than dead, which is this check's
        # own doctrine — never claim a measurement it did not make.
        suffix = base[len(name) + 1 :].lower() if base.startswith(name + ".") else None
        if suffix in _OUT_OF_ROTATION_SUFFIXES:
            return word
    return None


def _invocable_kit_scripts() -> set[str]:
    """Kit script basenames a registration could plausibly INVOKE.

    Narrower than "every kit-owned file with a script extension", which swept in
    library modules — `paths.py`, `resolver.py`, `kitconfig.py`, `__init__.py`.
    Combined with a name match, that set claimed an adopter's own
    `scripts/my_hooks/env_paths.py`, and renaming their unrelated file produced
    `✗ NO SUCH FILE` and exit 1 with nothing to tell them why (panel,
    adversarial lens). Anything under a `lib/` is imported, never invoked.

    Defence in depth rather than the whole defence: the boundary check in
    `_match_word`'s basename comparison is what actually stops `env_paths.py`
    matching `paths.py`.
    This narrows the surface that check has to be right about.
    """
    return {
        PurePosixPath(rel).name
        for rel, role in KIT_OWNED
        if rel.endswith((".py", ".sh")) and "/lib/" not in rel and role != "template"
    }


def inspect_registrations(root: Path, engines_dir: str) -> list[RegistrationStatus]:
    """Whether each runtime's hook registration names a path that exists.

    Derived from `KIT_OWNED` rather than from a list of hook names: an adopter
    registering `check_doc_budget.py` on `SessionStart` gets the same check as
    one registering `pr_followup_hook.py` on `PostToolUse`, and adding a kit
    script does not require remembering to add it here too.
    """
    # Scripts a registration could plausibly INVOKE, not every kit-owned file
    # with a script extension. The wider set swept in library modules —
    # `paths.py`, `resolver.py`, `kitconfig.py`, `__init__.py` — and combined
    # with a substring match that turned an adopter's own
    # `scripts/my_hooks/env_paths.py` into a "kit hook" (it ends in `paths.py`).
    # Renaming their own unrelated file then produced `✗ NO SUCH FILE` and exit
    # 1, permanently and with no way for them to know why (panel, adversarial
    # lens, delta round). Anything under a `lib/` is imported, never invoked.
    kit_scripts = _invocable_kit_scripts()
    statuses: list[RegistrationStatus] = []
    for runtime, surface, report_absent in REGISTRATION_SURFACES:
        path = root / surface
        if not path.is_file():
            if report_absent:
                statuses.append(RegistrationStatus(runtime, surface, "absent"))
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError, RecursionError) as exc:
            # Same degrade-don't-abort rule the baseline read follows: a
            # registration file this run could not parse is reported, never
            # raised. A diagnostic that dies on one malformed file tells the
            # adopter nothing about the other thirty-six.
            #
            # `RecursionError` belongs in this list and was the omission: a
            # VALID but degenerately nested document (thousands of `[[[…]]]`)
            # exhausts the stack inside `json.loads` itself, and the walk below
            # is capped for the same reason. Both were reachable, and both
            # produced a traceback where this line promises a report (panel,
            # adversarial lens, PR #389).
            statuses.append(RegistrationStatus(runtime, surface, "unreadable", str(exc)))
            continue
        try:
            commands = _hook_commands(document)
        except (_RegistrationTooDeep, RecursionError) as exc:
            # The walk gets the same treatment as the parse, and for the same
            # reason. `RecursionError` stays beside the cap because the cap is
            # this module's limit and the interpreter's is not the same number.
            statuses.append(RegistrationStatus(runtime, surface, "unreadable", str(exc)))
            continue
        found: list[RegistrationStatus] = []
        seen: set[str] = set()
        for command in commands:
            # Marking happens per WORD, inside `_script_words`, because whether a
            # placeholder expands depends on the quoting around it.
            lexed, words = _script_words(command)
            if not lexed:
                found.append(
                    RegistrationStatus(
                        runtime, surface, "unresolvable", "unbalanced quote — not lexable"
                    )
                )
                continue
            for name in sorted(kit_scripts):
                token = _match_word(words, name)
                if token is None or token in seen:
                    continue
                seen.add(token)
                if "$" in token:
                    # An expansion this check does not know. Saying so is the
                    # honest answer: `broken` would assert a file is missing
                    # from a path that was never resolved.
                    found.append(
                        RegistrationStatus(
                            runtime, surface, "unresolvable", token.replace(_ROOT_SENTINEL, "$ROOT")
                        )
                    )
                    continue
                target = Path(token.replace(_ROOT_SENTINEL, str(root)))
                if not target.is_absolute():
                    # A relative token is relative to the repo root: every shape
                    # the kit prints either interpolates the root or `cd`s to it
                    # first.
                    target = root / target
                try:
                    shown = str(target.relative_to(root))
                except ValueError:
                    shown = str(target)
                found.append(
                    RegistrationStatus(
                        runtime,
                        surface,
                        "resolves" if target.is_file() else "broken",
                        shown,
                    )
                )
        if not found and report_absent:
            # A registration file with no kit script in it. Not an error: the
            # adopter may have declined the hook, and `/hooks` in a live session
            # is the only authority on what a runtime actually loaded. Silent for
            # the optional overlay, which carries a registration only if the
            # adopter chose to put one there.
            found.append(
                RegistrationStatus(runtime, surface, "unregistered", f"engines: {engines_dir}")
            )
        statuses.extend(found)
    return statuses


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
    twenty-seven empty lists to read past in every manifest diff (32 KIT_OWNED
    entries, 5 with a dependent; the earlier figure of "thirty" was a guess and
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
    # NOTE the absent `kit_commit`. This is the kit's RELEASE manifest — "what
    # the kit ships" — and deliberately not a baseline, which is "what a repo
    # installed". Three reasons it must not carry the field:
    #
    # 1. It cannot be filled here without lying. This manifest is COMMITTED, so
    #    the only sha available at generation is the parent commit's, never the
    #    one that will carry it. A value always one commit stale is worse than
    #    no value, because a reader would take it literally.
    # 2. Filling it would break the CI drift gate. `--generate-manifest` has to
    #    be byte-deterministic for a given tree; a HEAD sha changes on every
    #    commit, so the self-check would fail on every PR and the gate would be
    #    switched off rather than fixed.
    # 3. It keeps a copied release manifest from impersonating a baseline. The
    #    `cp -r` quickstart (#18) puts this file in an adopter verbatim, and
    #    `_baseline_trusted` keys on the field's PRESENCE. Were it present here,
    #    that copy would be trusted as a record of an install it knows nothing
    #    about — and every file installed at an older version would read as a
    #    local edit, which is #51 reproduced by the fix for #51.
    #
    # `--record-install` is the only writer of that field, which is what makes
    # its presence mean "some kit actually recorded an install here".
    return {
        "kit_version": kit_version,
        "files": files,
        "adopter_owned": list(ADOPTER_OWNED),
    }


def _was_written_by_record_install(candidate: object) -> bool:
    """Whether this JSON is a file `--record-install` wrote.

    ONE signal, and it is exact: `record_install_manifest` always emits the
    ``kit_commit`` key (its value may be null; the key is not optional), and
    `generate_manifest` never does. So the key's presence is a complete answer
    to "did this mode write this file", not a heuristic.

    An earlier version required a SECOND signal — at least one ``required_by``
    entry — to classify a release manifest. That was the same mistake this whole
    engine exists to stop: ``required_by`` is not a property `generate_manifest`
    guarantees, it is an emergent fact about the current Python import graph
    (today 5 of 32 kit-owned files have a dependent). A kit whose graph loses
    its last shared-library edge produces a release manifest with no
    ``required_by``, the guard silently stops recognising it, and
    `--record-install --root <the kit's own checkout>` destroys it again — exit
    0, success message, reproduced by the panel by stripping those keys from
    the real manifest. A guard resting on an incidental property of today's
    codebase is not a guard.

    This is deliberately the SAME signal `_baseline_trusted` reads. One concept
    — "a baseline is a file this mode wrote" — so the two cannot drift apart.
    """
    return isinstance(candidate, dict) and "kit_commit" in candidate


def _git_head(checkout: Path) -> str | None:
    """Resolve a checkout's HEAD commit, or None if that is not answerable.

    Only ever called from `--record-install`, never from the read path, so a
    missing git binary degrades the provenance field to null and cannot break
    the diagnostic itself. `rev-parse HEAD` rather than reading `.git/HEAD` by
    hand: the latter has to special-case packed refs, worktrees (`.git` is a
    file, not a directory) and detached HEAD, and getting any of them wrong
    would stamp a *wrong* sha, which is worse than stamping none.
    """
    try:
        done = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    sha = done.stdout.strip()
    # Verified rather than assumed: `rev-parse` prints its ARGUMENT back on a
    # path that is not a repository ("HEAD\n", exit 128), so an exit check alone
    # is not enough to know a sha came back.
    #
    # Both widths are real HEADs: 40 hex in a SHA-1 repository, 64 in one
    # created with `--object-format=sha256`. Matching only the former refuses a
    # valid checkout and reports it as "not a git checkout" (CodeRabbit, PR
    # #278).
    if done.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
        return None
    return sha


def record_install_manifest(
    root: Path,
    config: dict,
    kit_version: int,
    kit_commit: str | None,
    source_files: dict | None = None,
) -> tuple[dict, list[str]]:
    """Record what is ACTUALLY INSTALLED in an adopter as its drift baseline.

    This is the step that was missing, and its absence is why the three-way
    split below could not be trusted. `/adopt` and `/upgrade` copy kit files in
    and never write this file, so an adopter's `kit-manifest.json` stays at
    whatever it was on the day it first arrived. Measured on a real adopter
    (2026-08-03): its manifest recorded `wrap-up.md` at the kit's 2026-07-15
    version while the file beside it had been installed from a 2026-08-03
    commit — a baseline nineteen days behind the tree it claims to describe.
    Compared against that, an unmodified file reads as a local edit, which is
    the exact false accusation #51 was filed about.

    **Hashes come from the adopter's own files, not from the kit's manifest**,
    and the distinction is the whole point. The baseline answers "what is
    installed here", so that a later mismatch means someone edited it. Copying
    the kit's hashes instead would assert "these files came from kit HEAD",
    which is false for any install that is merely old — and would re-file every
    stale file as an edit, reproducing the bug in a new place.

    `kit_commit` is provenance, recorded separately and allowed to be None: an
    install being retro-recorded genuinely does not know which kit it came
    from. That does not weaken the edit axis (the hashes were just taken from
    the files), only the "am I behind upstream" question, which needs the
    comparison manifest anyway.

    **`source_files` is what keeps this from blessing a file the kit never
    installed**, and the two modes are deliberately different (CodeRabbit, PR
    #278):

    - **Given** (`--from-kit`): the caller is asserting "I just installed these
      from that kit", so a file is recorded only if it MATCHES that kit's
      manifest. `/adopt` copies only where the target does not already exist,
      so an adopter's own pre-existing file at a kit-owned path is retained,
      not copied — and hashing it here would record it as kit-installed. On the
      next upgrade it would then read `STALE`, whose wording is "replace them,
      nothing local is lost", and the operator would be told to overwrite their
      own file. Non-matching paths are returned as the second element and left
      out, so they stay unjudgeable rather than confidently wrong.
    - **Omitted**: retro-recording an existing install, where nothing matches
      current HEAD by construction and the operator is explicitly taking the
      files as found. Everything installed is recorded.
    """
    engines_dir = str(get(config, "paths.engines", KIT_ENGINE_PREFIX))
    files: dict[str, dict] = {}
    unverified: list[str] = []
    not_installed: list[str] = []
    for rel, role in KIT_OWNED:
        target = root / _remap(rel, engines_dir)
        # Keyed by the KIT-layout path even when the file lives somewhere else
        # locally, so this manifest and the kit's are keyed identically and
        # `inspect` can look both up with one key. The remap is applied to the
        # lookup, never to the key.
        if not target.is_file():
            # The declared install set (#286), recorded rather than asked for:
            # this loop already walks every kit-owned path and already knows
            # which ones are absent — it just dropped that fact. Keeping it is
            # what lets a later run tell a deliberate omission from a deletion.
            not_installed.append(rel)
            continue
        digest = sha256_of(target)
        if source_files is not None:
            # Same non-dict hazard as the caller's, one level down: a `files`
            # value that is a non-empty list survives `or {}` and raises on
            # `.get`. Anything that is not a matching dict entry means "this did
            # not come from that kit", which is the conservative answer.
            entry = source_files.get(rel) if isinstance(source_files, dict) else None
            if not isinstance(entry, dict) or entry.get("sha256") != digest:
                unverified.append(_remap(rel, engines_dir))
                continue
        files[rel] = {"sha256": digest, "role": role}
    recorded = {
        "kit_version": kit_version,
        "kit_commit": kit_commit,
        "files": files,
        "adopter_owned": list(ADOPTER_OWNED),
    }
    # `not_installed` is written ONLY when this record is complete, and an
    # `unverified` path is exactly what makes it incomplete: that path is
    # present but matched no source-kit file, so it is deliberately in neither
    # map. An earlier version wrote the key anyway, reasoning that a present
    # file will never be asked about — true when the record is written, and
    # false the moment someone deletes it. `inspect` would then find it absent,
    # in neither map, and call it `new-upstream`: "the kit added this since your
    # baseline", asserted confidently about the adopter's own deleted file, and
    # exiting 0. (CodeRabbit, PR #322.)
    #
    # Omitting the key degrades that path to plain `missing` — ambiguous, but
    # ambiguous is what a partial record has earned, and the report already
    # names the command that completes it. Same rule as the read side: the key
    # must be PRESENT to claim a scope, so a scope that cannot be claimed
    # honestly is not claimed at all. `--record-install` also exits 1 here and
    # lists the unverified paths on stderr, so this is never silent.
    if not unverified:
        recorded["not_installed"] = not_installed
    return recorded, unverified


def _declared_scope(baseline: dict | None, trusted: bool) -> set[str] | None:
    """The paths this repo recorded as deliberately not installed, or None.

    None means "no declared set" and is NOT the same as an empty one: an empty
    set is a full install (every kit-owned path present at record time), while
    None is a baseline that never recorded the axis at all. They must report
    differently — the first can say "intact", the second cannot say anything.

    Requires `trusted`, for the same reason `_drift_state` does: an untrusted
    baseline's contents cannot carry a claim about what happened after it was
    written, and "declined" is exactly such a claim.

    A non-list value degrades to None rather than raising — the same
    degrade-don't-abort rule the `files` handling in `inspect` follows, and for
    the same reason: this is a read-only diagnostic, and a malformed key in one
    axis must not take the whole report down with it.
    """
    if not trusted:
        return None
    declared = (baseline or {}).get("not_installed")
    if not isinstance(declared, list):
        return None
    # The `files` map must be READABLE too, not merely present — the two halves
    # are one record and a scope claim needs both. `inspect` degrades a non-dict
    # `files` to `{}`, so without this check a baseline carrying a valid
    # `not_installed` beside a malformed `files` would classify every absent
    # file that WAS installed as `declined` (silent) or `new-upstream`
    # (informational) instead of `removed` (exit 1) — the malformed half
    # deciding the answer for the sound one. (CodeRabbit, PR #322.)
    if not isinstance((baseline or {}).get("files"), dict):
        return None
    return {item for item in declared if isinstance(item, str)}


def _baseline_trusted(baseline: dict | None) -> bool:
    """Whether a baseline manifest's hashes can carry a local-edit claim.

    The signal is the PRESENCE of `kit_commit`, not its value. Presence means
    the manifest was written by a kit that refreshes the baseline on install
    (`--record-install`), so a file that no longer matches it was changed after
    it was recorded — the only reading under which "locally edited" is a fact
    rather than a guess. A manifest predating this field has no key and is
    distrusted, which degrades the report to the pre-#51 `differs` wording
    instead of making a confident wrong claim.

    Keyed on presence rather than value because a legitimately recorded
    baseline may carry `kit_commit: null` (an existing install recorded
    retroactively knows its hashes but not its origin). Reading the VALUE as
    the signal would throw that case away and, worse, would trust the kit's own
    release manifest for provenance it deliberately leaves null.
    """
    return isinstance(baseline, dict) and "kit_commit" in baseline


def _drift_state(actual: str, expected: str, recorded: str | None) -> tuple[str, str]:
    """Split one hash mismatch into its cause, given a trusted baseline.

    `expected` is the comparison manifest's hash (what the kit ships now);
    `recorded` is the baseline's (what this repo installed). `recorded` is None
    when the baseline has no entry for the file at all — installed after the
    baseline was recorded — which is unjudgeable and says so.

    The four-way table from #51, per file rather than per repo. Using the
    comparison manifest's hash directly (rather than a repo-level "is my commit
    behind") is what makes it exact: a repo one commit behind upstream has
    almost always had ONE file change, and a repo-level `behind` would tar
    every other differing file with it.
    """
    if recorded is None:
        return "differs", f"{actual[:12]} != {expected[:12]}, not in baseline"
    if actual == recorded:
        # Untouched since install, and upstream has moved past it.
        return "stale", f"installed {actual[:12]}, kit ships {expected[:12]}"
    if recorded == expected:
        # Upstream never moved; the local file did.
        return "locally-edited", f"installed {recorded[:12]}, now {actual[:12]}"
    return (
        "stale-and-edited",
        f"installed {recorded[:12]}, now {actual[:12]}, kit ships {expected[:12]}",
    )


def inspect(
    root: Path,
    manifest: dict,
    config: dict,
    baseline: dict | None = None,
    *,
    baseline_is_comparison: bool = False,
) -> Report:
    engines_dir = str(get(config, "paths.engines", KIT_ENGINE_PREFIX))
    manifest_files = manifest.get("files") or {}
    trusted = _baseline_trusted(baseline)
    # `isinstance`, not `or {}`: a non-empty list or string is truthy, so `or`
    # passes it straight through to `.get` below and raises AttributeError,
    # aborting the whole read-only diagnostic. That is the same
    # degrade-don't-abort violation the `kit_commit` normalization exists to
    # prevent, reached through the same trust gate — and the minimal hand-edit
    # that turns trust ON (`"kit_commit": null`) is what makes this path
    # reachable at all (panel, adversarial lens).
    raw_baseline_files = (baseline or {}).get("files") if trusted else None
    baseline_files = raw_baseline_files if isinstance(raw_baseline_files, dict) else {}
    declared_scope = _declared_scope(baseline, trusted)

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
                # FIRST, ahead of the declared set: an engine that is installed
                # needs this file, so the install is broken whatever the record
                # says about intent. A path recorded as declined AND required by
                # something installed is a contradiction, and the safe reading
                # of a contradiction is the loud one.
                names = ", ".join(PurePosixPath(dep).name for dep in needed_by)
                statuses.append(
                    FileStatus(local_rel, role, "missing-required", f"needed by {names}")
                )
            elif declared_scope is None:
                # No declared set — the pre-#286 answer, unchanged and
                # deliberately not improved by inference. `render` says why and
                # names the command that fixes it.
                statuses.append(FileStatus(local_rel, role, "missing"))
            elif rel in baseline_files:
                # Recorded as INSTALLED and now absent. Checked before the
                # declared set so a malformed baseline listing a path in both
                # resolves to the finding rather than to silence.
                statuses.append(
                    FileStatus(local_rel, role, "removed", "recorded as installed in this baseline")
                )
            elif rel in declared_scope:
                statuses.append(
                    FileStatus(local_rel, role, "declined", "absent when the baseline was recorded")
                )
            else:
                # In neither map: the baseline predates the file's existence in
                # the kit. Not an omission the adopter chose — one they were
                # never offered.
                statuses.append(
                    FileStatus(
                        local_rel, role, "new-upstream", "added to the kit since this baseline"
                    )
                )
            continue
        if expected is None:
            statuses.append(FileStatus(local_rel, role, "unknown-version", "no manifest entry"))
            continue
        actual = sha256_of(target)
        if actual == expected:
            # Defined against the COMPARISON manifest alone, deliberately: a
            # file matching what the kit ships needs no action whatever the
            # baseline says. This also absorbs the hand-updated case (edited,
            # but edited into agreement with upstream) as `unchanged`, which is
            # the correct instruction even though the baseline is out of date.
            statuses.append(FileStatus(local_rel, role, "unchanged"))
        elif trusted:
            # Same reason as `baseline_files` above: a per-file entry that is
            # not a dict must degrade to "no baseline entry for this file"
            # (which `_drift_state` handles) rather than crash the report.
            recorded_entry = baseline_files.get(rel)
            state, detail = _drift_state(
                actual,
                expected,
                recorded_entry.get("sha256") if isinstance(recorded_entry, dict) else None,
            )
            statuses.append(FileStatus(local_rel, role, state, detail))
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
    # #381: the narrative check was never taught about `not_installed`, so an
    # adopter who deliberately declined the kit's `pre-push` was told to install
    # it on every run — three lines below the same report calling the adoption
    # intact with N files declined. That is #286's failure surviving in a second
    # code path, and its cost is not cosmetic: the decline can be permanent (the
    # kit's hook is all-or-nothing, #46), so the warning can never be cleared,
    # and a permanent warning is how the next real one gets skimmed past.
    #
    # Evidence order, not declaration order: an installed hook reports installed
    # even if the baseline declares otherwise, because the file on disk is the
    # stronger fact and a stale declaration must not hide a working install.
    if hooks_installed:
        hooks_state = "installed"
    elif declared_scope is not None and PRE_PUSH_REL in declared_scope:
        hooks_state = "declined"
    else:
        hooks_state = "not-installed"

    narrative: dict[str, bool] = {}
    targets = [get(config, key, None) for key in ("paths.handoff", "paths.friction_log")]
    # The two root entry points are seeded by the same `seed_doc` and gated by the
    # same predicate, so they belong to the same check — and `/upgrade` Step 1 now
    # says so in as many words. Omitting them left the failure this PR exists to
    # fix INVISIBLE to the tool whose job is finding it: a `cp -r` adopter whose
    # `./init.sh` never completed keeps the kit's own contract in both files, and
    # the doctor reported a clean bill of health (panel round 6, adversarial).
    #
    # Literal names, matching init.sh: unlike the narrative docs these are not
    # configurable — Claude Code reads `CLAUDE.md` at the repo root and nowhere
    # else, so there is no path key to resolve.
    targets += ["AGENTS.md", "CLAUDE.md"]
    for rel in targets:
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
        # TWO shapes where `doc.is_file()` alone said the wrong thing, both
        # reported by the review bot and both the divergence class above:
        #
        #   - a target that EXISTS but is not a regular file (a directory named
        #     AGENTS.md, a dangling symlink) is not a file, so it reported as
        #     "run ./init.sh" — which init.sh then refuses, leaving it
        #     "already in use — left untouched". Wrong advice, and the same
        #     no-op remedy round 2 removed. init.sh leaves such a target alone,
        #     so this reports it alone too.
        #   - an unreadable regular file raised OSError out of read_bytes and
        #     aborted the WHOLE report, while init.sh's guard fails safe. A
        #     diagnostic that dies on one unreadable file tells you nothing
        #     about the other thirty-two.
        #
        # Both now resolve the way init.sh resolves them: left alone. Neither
        # is *good* reporting — a directory named AGENTS.md is broken and this
        # says "in use" — but agreeing with init.sh is the property being
        # protected, and a third state is a Report shape change with JSON
        # consumers behind it. Filed rather than smuggled into a fix round.
        #
        # Superseded note, kept for the reader who finds the old wording
        # elsewhere: this divergence was previously recorded here as known,
        # unfiled, and deliberately unfixed — note
        # that pr_watch and pr_followup_hook both treat an unreadable config as
        # "must never raise", so this check is the outlier.
        if doc.exists() or doc.is_symlink():
            if not doc.is_file():
                narrative[str(rel)] = True  # not a regular file — init.sh leaves it
                continue
            try:
                first_line = doc.read_bytes().decode("utf-8", "replace").split("\n", 1)[0]
            except OSError:
                narrative[str(rel)] = True  # unreadable — init.sh's guard fails safe
                continue
            narrative[str(rel)] = not _still_a_skeleton(first_line)
        else:
            narrative[str(rel)] = False  # missing — init.sh WILL seed it

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
        hooks_state=hooks_state,
        registrations=inspect_registrations(root, engines_dir),
        narrative_rendered=narrative,
        baseline_trusted=trusted,
        declared_scope_known=declared_scope is not None,
        # Passed in rather than inferred from paths: `main` knows it from the
        # resolved PATHS, which this function does not see.
        #
        # But it is VERIFIED here rather than believed, because a caller that
        # gets it wrong produces a self-contradicting report: the summary says
        # "no upstream was consulted" while a file below it says "changed
        # upstream". A caller asserting self-comparison is asserting the two
        # documents are the same one, so that is exactly what is checked —
        # cheap, and it makes the invariant hold by construction instead of by
        # assumption (panel, adversarial lens).
        #
        # `and trusted` because an UNtrusted baseline was never consulted for a
        # cause at all, so "compared against itself" describes nothing that
        # happened.
        #
        # KNOWN GAP, deliberately documented rather than closed: `main` derives
        # its half with `Path.resolve()`, which follows symlinks but cannot see
        # HARD links — two hard links to one inode resolve to two different
        # paths, so that case reports as an ordinary independent baseline. The
        # content is identical either way, so no file is ever misattributed;
        # only the caveat goes missing. No `/adopt` or `/upgrade` step
        # constructs hard-linked manifests. Detecting it needs `st_ino`/`st_dev`
        # comparison, which is a new mechanism for a LOW with no reachable
        # consequence — the doctrine's answer to that is to document the
        # limitation, not to trade it for more machinery.
        baseline_is_comparison=(baseline_is_comparison and trusted and baseline == manifest),
        # Normalized to str-or-None. Trust keys on the KEY's presence, so any
        # JSON type survives it — and `render` slices this value, which would
        # raise TypeError on a number or a list and abort the whole report over
        # a hand-edited supplementary file. That would contradict the
        # degrade-don't-abort rule the unreadable-baseline path states
        # (CodeRabbit, PR #278). An unusable value keeps the baseline trusted —
        # the hashes are still good — and only drops the provenance line.
        baseline_kit_commit=(
            commit
            if trusted and isinstance(commit := (baseline or {}).get("kit_commit"), str)
            else None
        ),
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

    # Three states, three marks. `·` is deliberately not `⚠`: a decline this repo
    # RECORDED is a fact about a healthy adoption, and the old warning told the
    # operator to run `./init.sh` — which would install a hook they have a
    # standing reason to refuse (#381).
    hook_line = {
        "installed": "  ✓ pre-push hook: installed",
        "declined": "  · pre-push hook: declined (recorded in not_installed)",
        "not-installed": "  ⚠ pre-push hook: NOT installed — run ./init.sh",
    }
    lines.append(hook_line.get(report.hooks_state, hook_line["not-installed"]))

    # The registrations (#379). Reported per surface, and marked by what each
    # state means for the operator: a dead path is a defect, an absent
    # registration is a choice, and an unresolvable one is a limit of this check.
    for reg in report.registrations:
        mark, text = {
            "resolves": ("✓", f"{reg.detail} resolves"),
            "broken": ("✗", f"{reg.detail} — NO SUCH FILE, so this hook cannot fire"),
            "unresolvable": ("⚠", f"{reg.detail} — path not resolvable from here"),
            # The detail names the engines dir the check resolved, which is the
            # useful half when nothing is registered — it was computed and shown
            # only in `--json` (panel, correctness lens).
            "unregistered": ("·", f"no kit hook registered ({reg.detail})"),
            "absent": ("·", "not present — no registration on this runtime"),
            "unreadable": ("⚠", f"unreadable — {reg.detail}"),
        }.get(reg.state, ("⚠", reg.state))
        lines.append(f"  {mark} {reg.surface} [{reg.runtime}]: {text}")
    if any(reg.state in ("unregistered", "absent") for reg in report.registrations):
        # Said once, not per line: `init.sh` prints both blocks and writes
        # neither (#303), and only a live session can report what a runtime
        # actually loaded — so this check can say the path is there, never that
        # the runtime read it.
        lines.append(
            "    (registrations are hand-written — ./init.sh prints both blocks; "
            "`/hooks` in a session is the authority on what loaded)"
        )
    for doc, rendered in report.narrative_rendered.items():
        # An entry point that is still the KIT's own is a different fact from a
        # narrative skeleton that was never rendered, and the remedy reads
        # differently: the file is not blank, it is confidently wrong about this
        # repo. Same command, so the distinction is in the words only.
        if doc in ("AGENTS.md", "CLAUDE.md"):
            unrendered = "still the kit's own contract, not yours — run ./init.sh"
        else:
            unrendered = "still an unrendered template — run ./init.sh"
        lines.append(f"  {'✓' if rendered else '⚠'} {doc}: " + ("in use" if rendered else unrendered))

    by_state: dict[str, list[FileStatus]] = {}
    for f in report.files:
        by_state.setdefault(f.state, []).append(f)

    n_required_missing = len(by_state.get("missing-required", []))
    n_removed = len(by_state.get("removed", []))
    n_declined = len(by_state.get("declined", []))
    n_new_upstream = len(by_state.get("new-upstream", []))
    # `missing` counts the absences that are FINDINGS, which is what it always
    # meant — the change is that `declined` and `new-upstream` are no longer
    # among them, because they are now distinguishable. Counting them here would
    # keep #286's permanent number and merely footnote it, which is the shape
    # this issue exists to remove: a count an operator must remember to ignore
    # stops being read.
    #
    # The parenthetical is what says how much of that absence is breakage, and
    # is rendered only when non-zero, so a healthy install's summary line is
    # unchanged. (The comment that used to stand here said `missing` counts
    # "BOTH absent states" and that the total "does not change meaning" — true
    # before this axis existed, and flatly contradicting the paragraph above it
    # afterwards. CodeRabbit, PR #322.)
    n_absent = len(by_state.get("missing", [])) + n_required_missing + n_removed
    notes = []
    if n_required_missing:
        notes.append(f"{n_required_missing} required by an installed engine")
    if n_removed:
        notes.append(f"{n_removed} recorded as installed here")
    absent_note = f" ({', '.join(notes)})" if notes else ""
    # `differ` counts all four mismatch states, so this line keeps meaning "how
    # many kit files are not what the kit ships" whether or not the baseline
    # let them be split. The breakdown below names the causes; counting only
    # the undifferentiated state here would make a fully-split report read as
    # `0 differ` with four files listed under it.
    n_differ = sum(
        len(by_state.get(state, []))
        for state in ("differs", "stale", "locally-edited", "stale-and-edited")
    )
    lines.append("")
    lines.append(
        f"  files: {len(by_state.get('unchanged', []))} unchanged, "
        f"{n_differ} differ, "
        f"{n_absent} missing{absent_note}, "
        f"{len(by_state.get('unknown-version', []))} unknown"
    )
    # The line #286 asked for, and it only exists when the question can actually
    # be answered. "Intact" is a claim about the DECLARED set, so it needs one;
    # without a declared set the count above stays ambiguous and the baseline
    # block below says so instead.
    # `unknown-version` means the file IS PRESENT and its drift cannot be
    # judged — it is an absence of information, not an absence of a file. Two
    # consequences, and the first is what made the empty-adoption branch below
    # state a falsehood: a tree holding only unjudgeable files is not empty.
    #
    # The second is softer and applies to every branch: none of these verdicts
    # is an all-clear while some file's drift is unjudgeable, and both skill
    # docs tell an operator to skim for exactly this ✓/✗/⚠ line. So the verdict
    # keeps its own subject — the install SET, which is genuinely knowable here
    # — and carries the caveat rather than swallowing it.
    # (Fallback panel, correctness lens, round 2.)
    n_unjudgeable = len(by_state.get("unknown-version", []))
    # BOTH kinds of present-file drift, not just the unjudgeable one. An earlier
    # version caveated `unknown-version` and left `n_differ` out, so a STALE or
    # LOCALLY EDITED file — drift the report HAS judged, and the actionable kind
    # — sat directly under a bare `✓ intact for this adoption` while the exit
    # code was 1. That is the weaker case getting the caveat and the stronger
    # one going without, in a line both skill docs tell an operator to skim.
    # (Panel, adversarial lens, round 3.)
    attention = []
    if n_differ:
        attention.append(f"{n_differ} present file(s) differ from the kit")
    if n_unjudgeable:
        attention.append(f"drift unjudgeable for {n_unjudgeable} present file(s)")
    caveat = f" ({', '.join(attention)}, listed below)" if attention else ""
    verdict_mark = "⚠" if attention else "✓"
    if report.declared_scope_known:
        if report.broken:
            # Never "intact" while something is absent that should not be —
            # the whole point of the split is that this case is now audible.
            #
            # Says "should be installed" and NOT "recorded as installed here",
            # which an earlier draft did: `broken` holds TWO states with
            # different provenance, and only `removed` comes from the baseline.
            # A `missing-required` file may be one the repo recorded as
            # DECLINED — absent, required by an installed engine, and on record
            # as exactly the opposite of installed. The per-state sections below
            # each name their own source; this line must not pick one of them
            # and assert it for both (the overstatement class #54 tracks).
            declined_note = f", {n_declined} declined" if n_declined else ""
            lines.append(
                f"  ✗ NOT intact for this adoption — {n_absent} file(s) absent that should be "
                f"installed{declined_note}{caveat}"
            )
        elif not by_state.get("unchanged") and not n_differ and not n_unjudgeable:
            # "Intact" is a claim about an install set, and an EMPTY set has
            # nothing to be intact. Recording a tree where nothing was ever
            # copied produces a well-formed baseline declining all of
            # KIT_OWNED, which would otherwise print the same confident ✓ as a
            # healthy sized-down adoption — under a `✗ paths.engines` line
            # saying every workflow reference resolves to nothing.
            #
            # That reads WORSE than the wording it replaced: `missing
            # (sized-down adoption, or incomplete)` at least floated
            # "incomplete". Exit stays 0 — an empty adoption is not broken, and
            # the installation-level checks above already carry the ✗ — but
            # this line must not bless it. (Fallback panel, adversarial lens.)
            # "all N declined" is only true when `declined` accounts for every
            # absence. With `new-upstream` files it is false, and at 0 declined
            # it read "all 0 kit-owned file(s) are declined" directly above an
            # itemised 33-file list — the headline/detail contradiction this
            # round closed twice for `removed`, reintroduced in the one
            # adjacent branch neither fix touched. (Panel, adversarial, r2.)
            breakdown = (
                f"{n_declined} declined and {n_new_upstream} never offered"
                if n_new_upstream
                else f"all {n_declined} kit-owned file(s) declined"
            )
            lines.append(
                f"  ⚠ nothing is installed here — {breakdown}, so this is an empty adoption "
                "rather than an intact one"
            )
        elif n_declined:
            lines.append(
                f"  {verdict_mark} intact for this adoption — "
                f"{n_declined} file(s) declined{caveat}"
            )
        else:
            lines.append(
                f"  {verdict_mark} intact for this adoption — full install, "
                f"nothing declined{caveat}"
            )
    if n_new_upstream:
        # Informational, and outside the intact/not-intact verdict on purpose:
        # these are neither installed nor declined, so they say nothing about
        # whether this repo is healthy. Listed by name because the count alone
        # is not actionable — the operator's next question is always "which".
        # States what is KNOWN — the baseline mentions these in neither map —
        # rather than the inference. "The kit added them since" is the ordinary
        # cause and not a fact this can establish: the same shape is what a
        # damaged baseline produces, and one deleted key turns a `removed`
        # finding into this reassuring line at exit 0. The baseline is the trust
        # root and is not integrity-protected (`_baseline_trusted` keys on the
        # PRESENCE of `kit_commit`), so no reading here can rule that out — but
        # the wording must not claim what only an intact record would support.
        # (Panel, adversarial lens, round 2.)
        lines.append(
            f"  ⓘ {n_new_upstream} file(s) this baseline does not mention either way — "
            "neither installed nor declined, so most likely added to the kit since it was "
            "recorded:"
        )
        for f in report.new_upstream:
            lines.append(f"      {f.path}")
        lines.append("      Run /upgrade to accept or decline them.")
    # ALWAYS emitted, in every combination. Both skill docs tell the operator to
    # read this line to confirm `--record-install` actually ran — and two
    # combinations used to print nothing at all (untrusted with zero mismatches;
    # trusted-without-provenance with zero mismatches), so the documented check
    # had a silent third outcome its two-way phrasing did not admit. A clean
    # install is exactly when someone wants to confirm the record landed
    # (panel, correctness lens).
    if report.baseline_trusted:
        origin = (
            f"installed from kit {report.baseline_kit_commit[:12]}"
            if report.baseline_kit_commit
            else "recorded, install provenance unknown"
        )
        if report.baseline_is_comparison:
            # No upstream in this run: the baseline IS the comparison, so a
            # mismatch means "edited since I recorded it" and nothing at all is
            # known about what the kit now ships.
            lines.append(
                f"  baseline: {origin} — compared against ITSELF, so staleness is not "
                "evaluated."
                "\n            Pass --manifest <kit checkout>/kit-manifest.json to see it."
            )
        elif n_differ:
            lines.append(f"  baseline: {origin} — mismatches below are split by cause")
        else:
            lines.append(f"  baseline: {origin}")
        # Gated on there being an ambiguous absence to explain. A full install
        # has nothing for the declared set to split, so the nudge would be pure
        # noise — which is the failure mode #286 is about, and reproducing it in
        # the fix's own advice line would be its own joke.
        if not report.declared_scope_known and by_state.get("missing"):
            # Says "declares no install set" rather than "predates" it, because
            # this cannot tell those apart and the second is often false. A
            # baseline written SECONDS AGO by a current kit lands here whenever
            # `--record-install` hit an unverified path: that suppresses
            # `not_installed` wholesale, while `kit_commit` is written anyway,
            # so the manifest is trusted, scope-less, and brand new. Both causes
            # reach this branch with identical evidence — an absent key — so the
            # note names both and lets the operator tell which.
            # (Panel, adversarial lens, round 4.)
            lines.append(
                "            This baseline declares no install set, so a deliberate omission\n"
                "            cannot be told from a deletion. Commonly it predates the declared\n"
                "            set, or --record-install suppressed it because some present file\n"
                "            did not match the source kit; a malformed `files` or\n"
                "            `not_installed` value reads the same way. Re-run --record-install\n"
                "            — and if it reports unverified paths, reconcile those first."
            )
    else:
        lines.append(
            "  baseline: none recorded — cannot tell stale from locally edited."
            "\n            Run `kit_doctor.py --record-install --from-kit <kit checkout>`"
            "\n            to stamp one from what is installed now."
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
    if report.baseline_trusted:
        # A trusted baseline routes every mismatch it can judge into one of the
        # three states below, so anything still here is a file the baseline has
        # no entry for — installed after it was recorded. Naming that is more
        # use than the schema-version hedge, which this branch deliberately
        # bypasses: the hedge exists because the version signal is unsound
        # (#51), and having a real baseline is precisely the case where it need
        # not be consulted at all.
        differs_label = (
            "differ from the kit, and are not in this repo's baseline — installed "
            "after it was recorded, so stale-vs-edited is unjudgeable. Re-record with "
            "--record-install once these are settled"
        )
    elif cannot_narrow:
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
        # Beside `missing-required` because they carry the same verdict from a
        # different source: that one derives "should be here" from the import
        # graph, this one from what the repo itself recorded installing. Neither
        # is a sized-down adoption, which is the reading `missing` allowed.
        (
            "removed",
            "✗ NOT INSTALLED, but this repo's baseline records it AS installed — deleted "
            "since. Restore it, or re-run --record-install if the removal was deliberate",
        ),
        ("differs", differs_label),
        # The three split states. Each states a FACT rather than a likelihood,
        # which is what the baseline buys and why these read differently from
        # `differs_label` above: that one hedges because it must, these do not
        # because they need not.
        (
            "stale",
            "STALE — byte-identical to what was installed here, so nothing was edited. "
            "The kit has moved on; replace them, nothing local is lost",
        ),
        (
            "locally-edited",
            (
                # The second clause is a claim about the KIT's copy, and a
                # self-comparison run has no information about it — there is no
                # upstream in the comparison at all. Asserting it there is the
                # overstatement class this repo files under #54.
                "LOCALLY EDITED — changed here since it was recorded. Move each edit into "
                "config/dev-model.yaml, then take the kit's copy"
                if report.baseline_is_comparison
                else "LOCALLY EDITED — changed here since install, and the kit's version is "
                "unchanged. Move each edit into config/dev-model.yaml, then take the kit's copy"
            ),
        ),
        (
            "stale-and-edited",
            "STALE **and** LOCALLY EDITED — changed here AND changed upstream. "
            "Diff against both before replacing; this is the only case that can lose work",
        ),
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
    #
    # With a trusted baseline the nudge keys on `locally-edited` instead, which
    # is the state it was always trying to name — the schema-version route was
    # only ever a proxy for it, and the wrong one (#51).
    show_nudge = (
        bool(by_state.get("locally-edited") or by_state.get("stale-and-edited"))
        if report.baseline_trusted
        else (by_state.get("differs") and not behind and not cannot_narrow)
    )
    if show_nudge:
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
    parser.add_argument(
        "--record-install",
        action="store_true",
        help="(adopter) record installed files as the drift baseline, after installing",
    )
    parser.add_argument(
        "--from-kit",
        type=Path,
        default=None,
        help="kit checkout this install came from; its HEAD is stamped as kit_commit",
    )
    parser.add_argument("--root", type=Path, default=None, help="repo root (default: discovered)")
    parser.add_argument(
        "--manifest", type=Path, default=None, help="manifest to COMPARE against (the kit's)"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="this repo's own installed-state manifest (default: <root>/kit-manifest.json)",
    )
    args = parser.parse_args(argv)

    root = (args.root or repo_root()).resolve()
    manifest_path = args.manifest or (root / MANIFEST_NAME)
    # Defaults to the adopter's OWN manifest, which is what makes `/upgrade`
    # Step 1 (`--manifest <kit clone>/kit-manifest.json`, no other flag) do the
    # three-way split with no change to the command anyone already runs. When
    # neither flag is passed both resolve to the same file — the self-check —
    # and the split correctly reduces to "any mismatch is a local edit".
    baseline_path = args.baseline or (root / MANIFEST_NAME)

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

    if args.record_install:
        # Before anything else: refuse to overwrite a RELEASE manifest. Checked
        # first because the damage is the write itself, and every later step
        # here (version parse, HEAD resolution, hashing) is wasted if we are
        # about to refuse anyway.
        if baseline_path.is_file():
            try:
                existing = json.loads(baseline_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                # Unreadable is not a release manifest as far as this check can
                # tell, and overwriting a corrupt baseline is the point of
                # re-recording. Fall through.
                existing = None
            if existing is not None and not _was_written_by_record_install(existing):
                print(
                    f"error: {baseline_path} was not written by --record-install "
                    "(it carries no kit_commit key), so it is not an install baseline — "
                    "refusing to overwrite it.",
                    file=sys.stderr,
                )
                print(
                    "hint: in the kit's own checkout you want --generate-manifest. In an "
                    "adopter that copied the kit's manifest in, delete it first: a copied "
                    "release manifest is not a baseline and is already ignored as one.",
                    file=sys.stderr,
                )
                return 2
        raw_version = get(config, "kit.version", None)
        version = 2 if raw_version is None else _as_version(raw_version)
        if version is None:
            print(
                f"error: kit.version is {raw_version!r}, expected an unquoted or quoted "
                "integer — refusing to stamp a baseline with a guessed version",
                file=sys.stderr,
            )
            return 2
        kit_commit = _git_head(args.from_kit.resolve()) if args.from_kit else None
        if args.from_kit and kit_commit is None:
            # Refuse rather than silently record null: the operator NAMED a
            # checkout, so a null here would answer a question they explicitly
            # asked, with the one value that means "nobody asked".
            print(
                f"error: cannot resolve HEAD of {args.from_kit} — not a git checkout, "
                "or git is unavailable",
                file=sys.stderr,
            )
            return 2
        source_files: dict | None = None
        if args.from_kit:
            source_manifest = args.from_kit / MANIFEST_NAME
            try:
                parsed_source = json.loads(source_manifest.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                # Refuse rather than fall back to recording everything: without
                # this manifest the retained-file check below cannot run, and
                # silently downgrading to the permissive mode is how a retained
                # adopter file gets blessed as kit-installed.
                print(f"error: cannot read {source_manifest}: {exc}", file=sys.stderr)
                return 2
            # TWO checks, and the second is what makes the first safe.
            #
            # Outer: syntactically valid JSON whose top level is anything
            # other than an object — a list, string, number, bool or null — has
            # no `.get`, and AttributeError is not in the `except` above, so the
            # tool tracebacked where every other malformed-input path in this
            # file degrades (CodeRabbit, PR #278). Stated as "not a dict" rather
            # than by example: `isinstance` treats every non-dict alike, so an
            # enumeration here can only go stale or read as exhaustive.
            #
            # Inner: `.get("files")` returns None for a dict with no `files`
            # key, or an explicit `"files": null` — and downstream, **None is
            # the sentinel for "no --from-kit was given"**, which turns
            # verification OFF entirely. The first version of this degrade
            # dropped the `or {}` it replaced and so reopened exactly the hole
            # the flag exists to close: `--from-kit` at a manifest with no
            # `files` key recorded every present kit-owned path as installed
            # from that kit, including a file the adopter had all along, at exit
            # 0 with no warning — which a later run then reports STALE, whose
            # instruction is "replace them, nothing local is lost". Found on a
            # live adopter upgrade, PR in-parallel-oy/cs-toolkit#1835.
            #
            # So once `--from-kit` is given this must be a dict, always. An
            # empty one is the safe value: it matches nothing, so every present
            # file lands in `unverified` and none is blessed.
            raw_source_files = parsed_source.get("files") if isinstance(parsed_source, dict) else None
            source_files = raw_source_files if isinstance(raw_source_files, dict) else {}
        baseline, unverified = record_install_manifest(
            root, config, version, kit_commit, source_files
        )
        try:
            baseline_path.write_text(
                json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            # Operator-facing failure, so it reports and exits 2 rather than
            # tracebacking — the convention the config and manifest read paths
            # above already follow (CodeRabbit, PR #278).
            print(f"error: cannot write baseline {baseline_path}: {exc}", file=sys.stderr)
            return 2
        origin = kit_commit[:12] if kit_commit else "unrecorded"
        print(
            f"wrote {baseline_path} ({len(baseline['files'])} installed files, "
            f"kit_version={version}, kit_commit={origin})"
        )
        if unverified:
            print(
                f"note: {len(unverified)} kit-owned path(s) present here do NOT match "
                f"{args.from_kit}, so they were left OUT of the baseline rather than "
                "recorded as installed from it — a file this kit did not put there must "
                "never be reported STALE and replaced. Refresh or reconcile each, then "
                "re-run:",
                file=sys.stderr,
            )
            for path in unverified:
                print(f"  · {path}", file=sys.stderr)
        if kit_commit is None:
            print(
                "note: no --from-kit given, so install provenance is unrecorded. Drift is "
                "still split into stale vs locally-edited (that uses the hashes, not the "
                "commit); only the 'how far behind upstream' question needs it.",
                file=sys.stderr,
            )
        # Non-zero when the record is PARTIAL. The baseline was written, so this
        # is not a failure to write — it is "I did not record everything you
        # have", and a caller that reads only the status code would otherwise
        # treat a partial record as a complete one and move on. `/adopt` and
        # `/upgrade` are agent-driven, which is exactly that caller (panel,
        # adversarial lens).
        return 1 if unverified else 0

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

    # A baseline is OPTIONAL and its absence is never fatal — an adopter that
    # has never recorded one still gets the pre-#51 report. Unreadable is
    # treated the same as absent rather than as an error, for the same reason:
    # this is a read-only diagnostic, and refusing to run because a
    # supplementary file is malformed would withhold the whole report over the
    # part of it that merely could not be refined. It IS reported, so the
    # degrade is visible rather than silent.
    baseline: dict | None = None
    baseline_is_comparison = baseline_path.resolve() == manifest_path.resolve()
    if baseline_is_comparison:
        # Same file, already read. Re-reading would be a second chance to
        # disagree with itself if it changed underneath us mid-run.
        baseline = manifest
    elif baseline_path.is_file():
        try:
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"warning: unreadable baseline {baseline_path}: {exc}", file=sys.stderr)
    if not isinstance(baseline, dict):
        baseline = None

    report = inspect(
        root, manifest, config, baseline, baseline_is_comparison=baseline_is_comparison
    )

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
                    # Beside `hooks_installed`, never instead of it: an existing
                    # consumer reading a bool must keep reading a bool, and the
                    # third state (#381) is what it could not previously see.
                    "hooks_state": report.hooks_state,
                    # #379. A consumer cannot derive this from `files`: the two
                    # registration surfaces are adopter-owned and are in neither
                    # `KIT_OWNED` nor any manifest, which is exactly why a
                    # byte-perfect install could report clean with a dead hook.
                    "registrations": [
                        {
                            "runtime": r.runtime,
                            "surface": r.surface,
                            "state": r.state,
                            "detail": r.detail,
                        }
                        for r in report.registrations
                    ],
                    "narrative_rendered": report.narrative_rendered,
                    # Both emitted, because a consumer cannot derive either from
                    # `files` alone: an all-`unchanged` report looks identical
                    # whether or not a baseline was consulted, and a null commit
                    # is a legitimate recorded value rather than an absent one.
                    "baseline_trusted": report.baseline_trusted,
                    "baseline_is_comparison": report.baseline_is_comparison,
                    "baseline_kit_commit": report.baseline_kit_commit,
                    # Not derivable from `files` either: a report with no absent
                    # file at all looks identical whether or not the declared
                    # set was available, and a consumer deciding whether to
                    # trust a `declined`/`missing` distinction needs to know.
                    "declared_scope_known": report.declared_scope_known,
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
    # `dead_registrations` joins the exit code for the reason #379 was filed:
    # the observable for a registration naming a path that is not there is a
    # hook that silently stopped firing, and until now nothing in the kit's own
    # instrument reported it. `broken` and `unreadable` reach here — see
    # `Report.dead_registrations` for why those two and not the other three.
    # (This said "only `broken`", written before `unreadable` joined the gate a
    # round later, and a lens caught the sentence still describing the older
    # behaviour — the same stale-prose class this session spent four PRs on.)
    return 1 if report.drifted or report.broken or report.dead_registrations else 0


if __name__ == "__main__":
    raise SystemExit(main())
