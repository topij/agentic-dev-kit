# REG-01 — the adoption fixture's runtime-registration scope and payloads

The exact decision this record asks for is **scope**, and it is unmade. The three
payloads below are drafted, digested and verified against the fixture's own installed
doctor in disposable copies; none of them has been written to the original fixture. No
initializer ran, no fixture file changed, and nothing here establishes what either
runtime loaded.

## Continuity, against the superseding baseline

`uv run python <scratch>/recheck_continuity_fix01.py`, retained as
[`recheck_continuity_fix01.py.txt`](adopt-reg01-evidence_2026-09-06/recheck_continuity_fix01.py.txt),
ran in `/Users/topi/Coding/agentic-dev-kit` at
`a4419dcd541f25162971615444aa995bc0dfb474` on 2026-09-06 UTC and exited zero. The
[result](adopt-reg01-evidence_2026-09-06/continuity-recheck.json) binds the read: the
comparison source matches its VER-02 input inventory and full Git state, and the fixture
matches [`fixture-inventory-after-fix01.json`](adopt-fix01-evidence_2026-09-06/fixture-inventory-after-fix01.json)
— the FIX-01 baseline, not the superseded VER-02/VER-03 one. Both generations of
retained evidence re-hash to their recorded digests.

**One expected divergence, named because it looks like drift and is not.** The program
compares the fixture's working-tree status against the VER-02 preflight and finds
exactly one new line, ` M AGENTS.md`. The other two FIX-01 files produce none, because
`.claude/agents/adversarial.md` and `.claude/agents/correctness.md` were already
untracked (`??`) before FIX-01 and editing an untracked file does not change its status
line. The first draft of this check asserted all three would appear and failed on that;
the assertion now derives the expected set from which approved paths were already
untracked, rather than assuming.

## The three payloads

All three registration paths are absent in the fixture — verified by direct inspection,
and by the doctor's own `· not present` lines for the two surfaces that report their
absence. Nothing below overwrites anything.

The fixture's `paths.engines` is `scripts/devkit`, and every path in every payload is
that value interpolated by `init.sh`'s own registration blocks. The command strings are
`init.sh`'s verbatim, not paraphrases of them.

| Path | Payload | `sha256` |
|---|---|---|
| `.codex/hooks.json` | [`payload-codex-hooks.json`](adopt-reg01-evidence_2026-09-06/payload-codex-hooks.json) | `dbea8d8084adcc50e786af584c7e407fc5d7040bf26bd614c9966e9ba2797cfb` |
| `.codex/config.toml` | [`payload-codex-config.toml`](adopt-reg01-evidence_2026-09-06/payload-codex-config.toml) | `d37497c3278121598a663564ab38b53f658969717f78decb661ddd11c66551ea` |
| `.claude/settings.json` | [`payload-claude-settings.json`](adopt-reg01-evidence_2026-09-06/payload-claude-settings.json) | `cafe367d9ec90f34644dec0a2a4929dc195962e16df332523b7a74fec82751bf` |

`.codex/hooks.json` registers `check_doc_budget.py` on `SessionStart` with no matcher
and a 15-second timeout, and `pr_followup_hook.py` on `PostToolUse` with matcher
`^Bash$` and a 10-second timeout. `.codex/config.toml` carries `[features] hooks = true`
and nothing else, so there is no inline registration for either engine to conflict with
the file. `.claude/settings.json` registers both budget tripwires on `SessionStart` with
no matcher and the follow-through hook on `PostToolUse` with matcher `Bash` and
`if: "Bash(*)"`, and carries the cockpit allow-list with `pr_watch.py` named at this
adopter's engines dir rather than the kit's own.

## What each scope buys, measured

Four disposable copies of the fixture, one per scope, each read by **its own** installed
doctor:
`python3 <copy>/scripts/devkit/kit_doctor.py --root <copy> --manifest
<comparison-source>/kit-manifest.json`, cwd the copy, driven from
`/Users/topi/Coding/agentic-dev-kit` at `a4419dcd541f25162971615444aa995bc0dfb474` on
2026-09-06 UTC. Every scope exited zero, including the do-nothing baseline. The
[captured reports](adopt-reg01-evidence_2026-09-06/registration-verification.json) are
the evidence and
[`verify_registration.py.txt`](adopt-reg01-evidence_2026-09-06/verify_registration.py.txt)
is the driver that produced them; it asserted the original fixture's inventory unchanged
around the whole run.

**The exit code does not discriminate between these scopes; only the report body does.**
That is the thing to decide on, and it is why the table below quotes lines rather than
statuses:

| Scope | What the report gains | What stays advisory |
|---|---|---|
| baseline | — | both `· not present` lines |
| codex-only | both Codex engine paths `resolves`, plus `check_doc_budget.py` and `pr_followup_hook.py` `canonical lifecycle form verified` | `· .claude/settings.json … not present` |
| claude-only | all three Claude engine paths `resolves` | `· .codex/hooks.json … not present` |
| both | every line from the two above | — |

The asymmetry is worth naming, because it is not a matter of taste. Only the **Codex**
surface gets a mechanical lifecycle verdict: `_codex_registration_semantics` checks
event, matcher, timeout and exact command string, and says so. The Claude surface is
checked for path resolution alone. Conversely, only the **Claude** surface carries the
cockpit allow-list, so `#606`'s ungranted check has nothing to read under codex-only.
Each single-runtime scope leaves the other's check unexercised.

## The green lines are load-bearing — the negative controls

A report that is green because nothing was examined is the failure mode this whole
exercise is exposed to, so each check was falsified before being relied on. Same command
shape, same revision and date as above; the captured reports retain each run, in two
sets — [`negative-controls.json`](adopt-reg01-evidence_2026-09-06/negative-controls.json)
for the controls on the checks the payloads rely on, driven by
[`negative_controls.py.txt`](adopt-reg01-evidence_2026-09-06/negative_controls.py.txt),
and [`negative-controls-2.json`](adopt-reg01-evidence_2026-09-06/negative-controls-2.json)
for the `[features]` probes below, driven by
[`negative_controls2.py.txt`](adopt-reg01-evidence_2026-09-06/negative_controls2.py.txt).

- **The kit's own default allow entry, in this adopter's layout.** Replacing
  `Bash(uv run scripts/devkit/pr_watch.py:*)` with the kit's `scripts/` spelling
  produced `· .claude/settings.json [claude]: no permissions.allow rule reaches
  scripts/devkit/pr_watch.py — nothing pre-approves it`. This is `#606` firing, and it
  is why the drafted payload's silence on that line means the grant is real rather than
  unchecked.
- **A wrong timeout.** `check_doc_budget.py` at 10 seconds instead of 15 produced
  `✗ … timeout must be 15 seconds — lifecycle wiring does not match` and **exit 1**.
- **An altered command string.** Dropping `exec` from the `PostToolUse` command removed
  that engine's `canonical lifecycle form verified` line and left exit 0. The verdict is
  withheld silently — recorded as an occurrence on
  [`#392`](https://github.com/topij/agentic-dev-kit/issues/392#issuecomment-5561503045)
  rather than re-filed, because that issue's option 3 is the fix for both axes.

The second set probes the axis the payload decision does **not** rest on, and is what
grounds [`#698`](https://github.com/topij/agentic-dev-kit/issues/698). Same command
shape, revision and date; each case keeps the canonical `.codex/hooks.json` and varies
only `.codex/config.toml`:

- **`[features] hooks = false`** and **`[features] codex_hooks = false`** each produced
  `✗ … Codex lifecycle hooks are disabled by the project config` and exit 1. The switch
  is graded when the doctor can see it.
- **`.codex/config.toml` absent entirely** produced no line about `[features]` at all,
  at exit 0, beneath four green Codex lines. That asymmetry — graded when the file
  exists, silent when it does not — is `#698`, and it is why the Codex scope below
  includes `config.toml` on `init.sh`'s instruction rather than on the doctor's demand.

## Recommended scope: both

Three reasons, in the order they matter:

1. **Neither single-runtime scope exercises the fixture's purpose.** This fixture exists
   to field-test adoption of a kit whose central doctrine is runtime parity. A fixture
   registered on one runtime is a fixture that has never demonstrated the two-runtime
   claim, and the remaining Phase 5 work rests on that claim.
2. **The two checks are disjoint, as measured above.** Codex-only leaves `#606`
   unexercised; Claude-only leaves every lifecycle verdict unexercised. Only both closes
   the pair, and the drafted payloads are already verified for both.
3. **Cost is symmetric and there is nothing to clobber.** All three paths are absent.

## What writing these would actually do, stated plainly

**`.claude/settings.json` is not an inert artifact.** A Claude Code session started in
the fixture would load it, register both `SessionStart` tripwires and the `PostToolUse`
hook, and apply the `permissions.allow` grants — including the `pr_watch.py` prefix
rule. That is the intended effect and it is the reason it is called out: approving this
scope approves a real permission grant in that tree, not only a file whose text a
diagnostic reads.

The Codex payloads are inert in the same sense only until a Codex session opens the
fixture and the project and its hook definitions are trusted through `/hooks`.

## Parked for one batched Codex session

**Nothing in this record states whether Codex loaded anything, and nothing here could.**
`/hooks` in a Codex session is the only authority. Parked for that session, together:

- Whether the drafted `.codex/hooks.json` and `.codex/config.toml` are loaded and
  trusted, once written under an approved scope.
- [`#698`](https://github.com/topij/agentic-dev-kit/issues/698)'s open question, filed
  this session: whether an unset `[features].hooks` stops Codex reading `hooks.json`.
  The issue is actionable under either answer, which is why it did not wait.
- The `#608` and `#255` dispositions, which rest on live Codex behaviour and stay
  reserved.

## Remaining boundary

This record decides nothing by itself. The scope above is a recommendation awaiting an
exact operator decision, and writing any payload into the fixture is a separate approval
from reading this.

The second Phase 5 blocker is untouched: the installed suite's initializer,
launcher-policy and portability failures in PR #686's retained terminal log still need
their bounded assessment, and the `test_lane_launcher.py` root-helper defect the handoff
identifies belongs to that assessment as a `#534` occurrence — deliberately not filed
here, because filing it from outside the assessment would commit the reading without the
log in front of it.

New initialization, adoption completion, fixture PR, Phase 5 exit and cs-toolkit replay
keep separate exact decisions. TRI-03/TRI-04/TRI-05 and the parked initializer proposal
remain reserved. No initializer ran and the original fixture was not written to under
REG-01.
