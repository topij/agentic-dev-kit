# Bounded assessment — the installed suite's failures in PR #686's retained log

The second open Phase 5 blocker. This assesses the retained log and re-measures the part
of it that the approved REG-01 application invalidated. It changes no fixture, runs no
initializer, and asks for no new ticket: everything it found belongs to
[`#534`](https://github.com/topij/agentic-dev-kit/issues/534)'s stated scope and is
[recorded there as an occurrence](https://github.com/topij/agentic-dev-kit/issues/534#issuecomment-5565697869).

## Boundary, stated first

Read-only against the original fixture. The one execution — a re-measurement — ran in a
**disposable copy**, and the program asserted the original fixture's inventory equal to
the REG-01 baseline before the copy and unchanged after the run. Nothing here advances
new initialization, adoption completion, the fixture PR, Phase 5 exit or the cs-toolkit
replay, each of which keeps its own exact decision.

[`assess_installed_suite.py.txt`](adopt-suite-assessment-evidence_2026-09-07/assess_installed_suite.py.txt)
is the program; it refuses to reuse an existing copy path rather than removing one.

## What the retained log contains

The log is `fixture-verification-output.json` in the PR #686 initialization evidence. Its
recorded `output_sha256` was re-verified against its own bytes before anything was read
out of it. It carries `79 failed, 2006 passed, 111 skipped in 388.78s (0:06:28)`, and the
[classification](adopt-suite-assessment-evidence_2026-09-07/retained-log-classification.json)
groups every failure line by file and maps each `FileNotFoundError` to the tests that
raised it.

**Every failure fits a cause `#534` already names.** `test_portability.py`'s are
runtime-parity-contract assertions about the kit's own workflows and adapters;
`test_kitconfig.py`'s are `test_shipped_skeletons_carry_the_unrendered_marker` reading the
kit's template skeletons, which an adopter renders to its own configured names. Both are
that issue's cause 1. `test_lane_launcher.py`'s single failure was already recorded there
during PR #691's panel, and is not re-filed here.

## The part REG-01 invalidated

Sixteen failure blocks in the log are `FileNotFoundError` on `<fixture>/.codex/hooks.json`
and `<fixture>/.claude/settings.json` — the two registration files that were **absent when
the log was taken and exist now**. The log is therefore stale as a description of the
fixture, and re-measuring against it rather than against the current state would be wrong.

Re-measured in the disposable copy on 2026-09-07 UTC, the registration-dependent selector
picked 15 items: **9 passed, 6 failed**. The
[captured run](adopt-suite-assessment-evidence_2026-09-07/post-reg01-registration-subset.json)
retains the command, both streams and the per-test outcomes.

**Neither outcome is an improvement on the failure it replaced**, which is the finding.

- The **9 passes** now assert against the *adopter's* registrations and report nothing
  about the kit's. That is `#534`'s silent-false-pass family — the shape its body calls
  "the failure mode worth prioritising" — reproduced nine times in one file. The
  direction of travel is the sharp part: these were loudly red until the adopter
  completed a step the kit's own installer told them to complete, and completing it is
  what silenced them.
- The **6 failures** share one mechanism. Each crosses an expectation built from
  `init.sh` run in the test's `tmp_path` sandbox — which initializes a fresh config and
  so takes the **default** `paths.engines: scripts` — against the repo's real
  registration file, which in this layout carries `scripts/devkit`. In the kit the two
  coincide, because the kit's engines dir is `scripts`. In an adopter whose engines dir
  differs they cannot, and the assertion text accuses the kit of advisory drift when the
  cause is the adopter's layout.

## Why this needed no new ticket

The occurrence route was the instruction and it is also the right one: `#534`'s
2026-09-06 comment already placed layout-assumption failures in scope including in files
its body does not name, and a PR #691 review round had already been corrected for reading
the body alone. Filing separately would have repeated that error.

It does add something to that issue's suggested scope, which the occurrence states: item
1's `_repo_layout` fix does not reach any of this. Nothing here reads
`REPO_ROOT / "scripts"`. The six read an engines dir that `init.sh` had just written with
its default; the nine read a correctly-resolved path that simply is not the kit's file in
an adopter. A test asserting a property of a file the kit *ships* needs the kit's copy of
it, not the path where an adopter keeps their own — and whether the answer is a
kit-repo-only marker or an installed reference copy is a decision the occurrence asks for
rather than settles.

## What this does not establish

It does not re-run the full installed suite, so it says nothing about whether the other
failures moved. It does not establish successful adoption verification, and a green
subset in a disposable copy is not a claim about the fixture. Nothing here observes what
either runtime loaded; `/hooks` remains the only authority, and that stays parked with
`#698`'s open question and the reserved `#608`/`#255` dispositions for one batched Codex
session.

## Remaining boundary

With this assessment done, both Phase 5 blockers named in the 2026-09-06 handoff are
closed out — registration by approved application, the installed suite by this
assessment. Phase 5 exit itself is a separate exact decision and is **not** taken here:
the suite's failures are now classified and recorded, not repaired, and the repairs
belong to `#534`.

New initialization, adoption completion, fixture PR, Phase 5 exit and cs-toolkit replay
keep separate exact decisions. TRI-03/TRI-04/TRI-05 and the parked initializer proposal
remain reserved.
