# FIX-01 — fixture ownership marker and lens definitions

The operator approved the exact FIX-01 scope with "Approved" on 2026-09-06, after the
proposal was prepared and presented in this session. This session executed it in Claude
Code. Its execution approval is consumed; the remaining fixture decisions are separate.

## What was applied

The retained [ownership/lens diff](codex-adopt-completion-review-evidence_2026-09-06/ownership-and-lenses.patch.json)
from the [continuation review](codex-adopt-completion-review_2026-09-06.md), extracted
verbatim to [`ownership-and-lenses.patch.txt`](adopt-fix01-evidence_2026-09-06/ownership-and-lenses.patch.txt)
(`417e4d4947bbef414a83389893e6b5d53cb7753331440e4ddd1f6d9ee96680a2`), applied to the
original adoption fixture. `AGENTS.md` loses its `<!-- devkit-source: kit-own -->` line
and keeps its policy body; `.claude/agents/adversarial.md` and
`.claude/agents/correctness.md` take the installed engine path in their description and
regeneration note. Model and effort are unchanged. No other fixture file was touched, no
commit was made in the fixture, and no initializer ran.

## Currency of the diff before applying

`git diff --name-only ab0a6d62308b298478b2f85fc961f14348f35365..HEAD` in
`/Users/topi/Coding/agentic-dev-kit` at `585483b6d6b65f01e6d98304a6ac0fde77bcbed7` on
2026-09-06 UTC listed, outside `saved_plans` and the four narrative records named by
`paths.handoff`, `paths.handoff_history`, `paths.friction_log` and
`paths.friction_log_archive`, `docs/agentic-dev-kit/workflows/adopt.md`,
`kit-manifest.json` and `scripts/tests/test_panel_prompt.py`. Naming the four keys
rather than saying "narrative" is deliberate: a review round read the shorter phrase as
covering the handoff alone and reported the friction log as an omission from the list. The landed VER-03 repair changed the test, not the
renderer: `scripts/panel_prompt.py`, its `config/dev-model.yaml` lens keys and the kit's
own `.claude/agents/` definitions are unchanged across that range. The retained diff was
therefore current against the kit as well as against the fixture.

The diff was also shown to be *complete* rather than merely applicable. Applying it to
copies of the three fixture files under the session scratch directory produced
`.claude/agents/adversarial.md` at
`f61adde9da0974c20dcba31d8fda4dec313e2f26ffd97baae518654bae3e9e7a` and
`.claude/agents/correctness.md` at
`a91ee86a18f6043d8f2cfba06cdbb983509ef9514b5924540f09b8a87d74e171` — byte-identical to
the fixture's own installed renderer output retained in the review's `inspection.json`.
There is no drift beyond the engine path.

## Preconditions and write boundary

`python3 .../scratchpad/recheck_continuity.py`, retained as
[`recheck_continuity.py.txt`](adopt-fix01-evidence_2026-09-06/recheck_continuity.py.txt),
is the VER-03 audit program with only its output path changed, so its `program_sha256`
differs from the retained original. Run in `/Users/topi/Coding/agentic-dev-kit` at
`585483b6d6b65f01e6d98304a6ac0fde77bcbed7` on 2026-09-06 UTC immediately before the
write, it exited zero with both inventories, both Git states and the legacy fixture
hashes matching; the [result](adopt-fix01-evidence_2026-09-06/continuity-pre-fix01.json)
binds that read.

**That result's own `command` field is wrong, and this paragraph is the correction.**
It reads `python3 /private/tmp/adk-ver03-7m5h8wtr/check_continuity.py` because the
VER-03 program hardcodes that string as a literal, and copying the program forward
carried the literal with it. The invocation was the scratch copy named above; the
`program_sha256` in the same file
(`7efc48bdf991151b11aaf5435187367e9f0074b2190d94b18077ada33d9a80bc`) is the digest of
the retained `recheck_continuity.py.txt` and not of the VER-03 original, so the two
fields disagree and the digest is the one to trust. A retained artifact that misreports
its own command is exactly what `AGENTS.md`'s stamp rule exists to prevent; the field is
left as the program emitted it rather than edited after the fact, and named here
instead. The fixture was on `chore/adopt-agentic-dev-kit` at
`08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` with no remote, and the destination `pwd` was
asserted before the write.

[`write-boundary.json`](adopt-fix01-evidence_2026-09-06/write-boundary.json) compares the
post-write fixture against the retained VER-02 input inventory: no path added, none
removed, and the changed set equal to the three approved files, each at unchanged mode.
The comparison source at `ab0a6d62308b298478b2f85fc961f14348f35365` is inventory-equal to
its retained input. The fixture head, branch and absent remote are recorded there; the
changes are uncommitted in the fixture, as approved.

## Doctor result

`python3 <fixture>/scripts/devkit/kit_doctor.py --root <fixture> --manifest
<comparison-source>/kit-manifest.json`, cwd the fixture, on 2026-09-06 UTC returned exit
zero. The [captured report](adopt-fix01-evidence_2026-09-06/doctor-after.json) reads
`AGENTS.md: in use` and both lens definitions as matching the running doctor's expected
output, where the review's retained report read `still the kit's own contract, not
yours — run ./init.sh` and `differs from the running doctor's expected output` for each
lens. The capture program asserted fixture inventory equality around the read.

## Why the marker removal, and not the doctor's own remedy

The doctor prints `run ./init.sh` for the ownership warning. `init.sh:2495` calls
`seed_doc "AGENTS" "AGENTS.md"`; with the marker on line 1 `_seedable` classifies the
file MARKED, which `seed_doc` renders `docs/templates/AGENTS.md.tmpl` over in default
mode (`init.sh:1936-1953`). The fixture policy survived the earlier field exercise only
because that run passed `--no-clobber`. Removing line 1 makes `_seedable` return IN USE,
which both modes leave untouched, so preservation stops depending on the flag.
`kit_doctor.py:570-595` keys the same judgement on line 1 against `SEED_MARKERS`
(`kit_doctor.py:560`) and is documented as having to agree with `_seedable` on every
input. Deleting line 1 to keep the content is the operator resolution
[`#338`](https://github.com/topij/agentic-dev-kit/issues/338) already names, so this is
that ticket's documented route rather than a new one.

## Continuity baseline is superseded

The retained VER-02/VER-03 fixture inventory no longer describes the fixture, by
approved change. The next session must compare against
[`fixture-inventory-after-fix01.json`](adopt-fix01-evidence_2026-09-06/fixture-inventory-after-fix01.json);
reading a mismatch against the older baseline as drift would be wrong. The comparison
source baseline is unchanged. Recheck continuity against the new baseline immediately
before any later approved execution.

## Remaining boundary

This applies fixture ownership and lens definitions only. Runtime registration remains
unchosen and all three registration paths remain absent; the doctor reports no
registration on either runtime, and file inspection cannot establish loaded hooks or
project trust. The installed suite's other failures still need their own bounded
assessment, and a warning-free doctor exit does not establish adoption completion.

New initialization, adoption completion, fixture PR, Phase 5 exit and cs-toolkit replay
keep separate exact decisions. TRI-03/TRI-04/TRI-05, `#608`/`#255` dispositions and the
parked initializer issue proposal remain reserved. No initializer ran and no tracker
write was performed under FIX-01.
