# REG-01 applied — runtime registration on both runtimes

The operator approved the REG-01 recommendation on 2026-09-07 — **both runtimes** — after
the [scope decision record](adopt-reg01-runtime-registration_2026-09-06.md) was prepared
and merged as PR #699. This session executed it. That execution approval is consumed;
the remaining fixture decisions are separate and untouched.

## What was applied

The three payloads retained in the [REG-01 evidence](adopt-reg01-evidence_2026-09-06/),
sourced from the committed copies rather than re-drafted, and re-hashed against that
directory's `sha256.json` before the write:

| Path | Payload | `sha256` |
|---|---|---|
| `.codex/hooks.json` | [`payload-codex-hooks.json`](adopt-reg01-evidence_2026-09-06/payload-codex-hooks.json) | `dbea8d8084adcc50e786af584c7e407fc5d7040bf26bd614c9966e9ba2797cfb` |
| `.codex/config.toml` | [`payload-codex-config.toml`](adopt-reg01-evidence_2026-09-06/payload-codex-config.toml) | `d37497c3278121598a663564ab38b53f658969717f78decb661ddd11c66551ea` |
| `.claude/settings.json` | [`payload-claude-settings.json`](adopt-reg01-evidence_2026-09-06/payload-claude-settings.json) | `cafe367d9ec90f34644dec0a2a4929dc195962e16df332523b7a74fec82751bf` |

`.codex/` did not exist and was created. No file was overwritten: the program asserted
each target absent before writing, and would have refused otherwise. No initializer ran,
and nothing was committed inside the fixture.

## Preconditions and write boundary

[`apply_reg01.py.txt`](adopt-reg01-application-evidence_2026-09-07/apply_reg01.py.txt) is
the program. It binds the kit, fixture and comparison-source roots to absolute paths,
asserts `cwd` before the first write, and verifies every payload **at the destination**
by re-hashing the file where it landed rather than trusting the copy to have worked —
the discipline `AGENTS.md`'s two-tree section asks for, applied because this session
wrote into a second tree.

Continuity was rechecked immediately before the write, not earlier in the session. The
[retained result](adopt-reg01-application-evidence_2026-09-07/continuity-recheck-2026-09-06.json)
ran in `/Users/topi/Coding/agentic-dev-kit` at
`810b2911abb1598b4662a5b96a6bcc5823588751` on 2026-09-07 UTC and exited zero, with the
fixture matching the FIX-01 baseline and the comparison source matching its VER-02 input
inventory.

**That file's name carries a date its content contradicts, and this paragraph is the
correction.** The retained continuity program hardcodes its output filename, so the file
says `2026-09-06` while its own `observed_at` reads `2026-09-07T03:55:05`. The
`observed_at` field is the authoritative one. The name is left as the program emitted it,
so that re-running the retained driver reproduces it, and named here instead — this is
the same class PR #699's correctness lens flagged in the previous evidence directory, so
it is called out rather than repeated silently.

[`write-boundary.json`](adopt-reg01-application-evidence_2026-09-07/write-boundary.json)
binds the boundary: the paths added are exactly `.codex`, `.codex/hooks.json`,
`.codex/config.toml` and `.claude/settings.json`; no path was removed; **no existing path
changed**; and the comparison source is inventory-equal across the write. The fixture's
`HEAD`, branch, absent remote and index are unchanged — the additions are untracked, as
`chore/adopt-agentic-dev-kit` at `08ac687f4ae14218a3861c6b8b143d8b86c4e3c2` with no
remote.

## Doctor result

`python3 <fixture>/scripts/devkit/kit_doctor.py --root <fixture> --manifest
<comparison-source>/kit-manifest.json`, cwd the fixture, on 2026-09-07 UTC returned exit
zero. The [captured report](adopt-reg01-application-evidence_2026-09-07/doctor-after-reg01.json)
carries no advisory `·` line at all: every engine path on both runtimes resolves, and
both Codex lifecycle forms read `canonical lifecycle form verified`. Where the
pre-application report read `· .claude/settings.json [claude]: not present` and
`· .codex/hooks.json [codex]: not present`, neither line remains. The program asserted
the fixture's inventory equal around the read.

**The disposable-copy trial predicted this exactly.** The `both` scope captured in PR
#699's [trial](adopt-reg01-evidence_2026-09-06/registration-verification.json) and the
real fixture's report are byte-identical once each run's own fixture root is normalised,
at the same exit code —
[`prediction-match.json`](adopt-reg01-application-evidence_2026-09-07/prediction-match.json)
binds that comparison and states the normalisation it performed. Verifying in a copy
first was not merely safe here; it was accurate.

## The new continuity baseline

**The FIX-01 baseline no longer describes the fixture, by approved change.** The next
session must compare against
[`fixture-inventory-after-reg01.json`](adopt-reg01-application-evidence_2026-09-07/fixture-inventory-after-reg01.json);
reading a mismatch against `fixture-inventory-after-fix01.json` as drift would be wrong,
exactly as the FIX-01 record said of its own predecessor. The comparison-source baseline
is unchanged. Recheck against the new baseline immediately before any later approved
execution.

## What this does and does not establish

`.claude/settings.json` is live in that tree: a Claude Code session opened in the fixture
would load both `SessionStart` tripwires, the `PostToolUse` follow-through hook, and the
`permissions.allow` grants including the `pr_watch.py` prefix rule. That consequence was
stated in the scope record before approval and is the thing the approval authorised.

**Nothing here states whether either runtime loaded anything, and nothing in this
repository could.** `/hooks` in a session is the only authority. The doctor reads files;
it cannot observe a client's trust step or its loaded set. The Codex payloads remain
inert until a Codex session opens the fixture and the project and its hook definitions
are trusted there.

A warning-free doctor exit does not establish adoption completion.

## Parked for one batched Codex session

- Whether the now-written `.codex/hooks.json` and `.codex/config.toml` load and are
  trusted, via `/hooks`.
- [`#698`](https://github.com/topij/agentic-dev-kit/issues/698)'s open question —
  whether an unset `[features].hooks` stops Codex reading `hooks.json`. This fixture now
  sets it to `true`, so the fixture no longer exercises the unset case that issue is
  about; `#698` still needs its answer independently.
- The `#608` and `#255` dispositions, which rest on live Codex behaviour.

## Remaining boundary

The installed suite's initializer, launcher-policy and portability failures in PR #686's
retained terminal log still need their bounded assessment; the `test_lane_launcher.py`
root-helper defect belongs to it as a `#534` occurrence, still deliberately unfiled from
outside that assessment.

New initialization, adoption completion, fixture PR, Phase 5 exit and cs-toolkit replay
keep separate exact decisions. TRI-03/TRI-04/TRI-05 and the parked initializer proposal
remain reserved. No initializer ran and no tracker write was performed under this
application.
