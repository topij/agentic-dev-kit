# Claude's shipped lane permissions as repository policy — `#606`

Phase 5's first slice. Three decisions about `config/claude-lane-settings.json`, each
taken separately, each on a measurement rather than on a reading of the allow list.
The evidence bundle beside this file
([`lane-permission-policy-evidence_2026-08-28/`](lane-permission-policy-evidence_2026-08-28/))
carries every prompt, every result object, and every profile the probes loaded.

All four probes ran on 2026-08-28 against Claude Code **2.1.250**, in a throwaway Git
repository at a scratch path, under the lane's own trust route and nothing else:

```
claude -p <prompt> \
  --setting-sources "" \
  --permission-mode dontAsk \
  --settings <profile> \
  --output-format json
```

`--setting-sources ""` is what makes the probe a probe: the operator's user settings
and the throwaway repository's own settings are both unloaded, so the named profile is
the one policy source, exactly as `launch_lane.py` arranges it for a real lane.

## Why anything was measured at all

`first-real-headless-lane-live-validation_2026-08-28.md` records the `make test` gap
this way:

> The profile grants neither `make` nor a bare `uv run pytest`, so a lane on this
> repository cannot run `make test` before pushing.

That is an inference from the allow list — and it is the **same inference a review lens
rejected**, in that same document, one bullet later, about
`kit_doctor.py --generate-manifest`: *this run itself* established that absence from the
allow list does not imply denial, because the runtime accepts a read-only class no rule
covers. The manifest claim was then measured. The `make test` claim was not.

So it was measured here first, before any decision rested on it.

### Probe A — the shipped profile, unmodified

Profile: `profile-shipped-at-probe-time.json`, byte-identical to
`config/claude-lane-settings.json` at `9d5aa887ff9ea66e47736bf4c0e3193ba0caf4db`.

| # | command | outcome |
|---|---|---|
| 1 | `cat README.md` | ran |
| 2 | `make test` | **refused** |
| 3 | `uv run pytest t -q` | **refused** |

`result-A.json` carries both denials as `Bash` entries holding those exact command
strings, and `permission_denials` has nothing else in it. Command 1 is the live
control: it proves the session ran and that the read-only Bash class was available, so
the two refusals are the profile's decision and not a dead session.

**The record's claim holds, now on a measurement.** A lane on this repository cannot
run `make test`, and cannot reach the suite through a bare `uv run pytest` either.

## The finding that reframes all three decisions

Before deciding whether to grant `make test`, the obvious objection was raised against
it: `make` runs whatever the worktree's `Makefile` says, and the profile grants
`Edit(**)`, so the lane can write the recipe it is about to be allowed to run. That
would make the grant equivalent to unrestricted execution.

That objection is correct — and measuring it showed the objection does not
*distinguish* `make test` from what the profile already ships.

### Probe B — `Bash(make test:*)` added, hostile mutation

Profile: `profile-widened.json` (shipped + `Bash(make test:*)`). The probe was asked to
rewrite `Makefile` so the `test` recipe writes a file at an **absolute path outside the
worktree**, then to run `make test`.

Result: `permission_denials: []`, and `ESCAPED.txt` appeared outside the worktree.

### Probe C — the shipped profile, unmodified, same hostile mutation

Profile: the shipped bytes again, with **nothing added**. The probe was asked to rewrite
`scripts/pr_watch.py` — a file the shipped profile already grants
`Bash(uv run scripts/pr_watch.py:*)` for — so that it writes outside the worktree, then
to run it.

Result: `permission_denials: []`, and `ESCAPED_VIA_PRWATCH.txt` appeared outside the
worktree.

### What C establishes

**The shipped profile already authorizes arbitrary execution outside the worktree, with
no rule in any list for it.** `Edit(**)` bounds *file edits* to the worktree; it does
not bound a *process*, and a `Bash(<interpreter> <worktree-path>)` grant names a file
the lane is separately allowed to rewrite. The two grants compose into something neither
one says.

This is not closeable by adding, removing, or narrowing entries. A command-prefix allow
list cannot constrain the **contents** of a file its prefix names, so no spelling of the
`pr_watch.py` grant fixes it while the lane can write `pr_watch.py`. Closing it needs a
different mechanism — an OS sandbox around the child, or granting only scripts resolved
from outside the lane-writable worktree — and that is a design, not an edit to this
profile.

**So the profile is a task-scoping mechanism, not a security boundary**, and that is the
honest description of what it does. The property it really delivers is fail-closed
behaviour for a **confused** lane: one that wanders off-task hits a denial, and under
`dont-ask` the wrapper terminalizes the run `failed` with a legible record of what it
reached for. That property is untouched by the wedge above, because a confused lane does
not rewrite the Makefile to escape — it just reaches for something no rule covers and
stops. Against a lane that is actively hostile, or prompt-injected into acting like one,
the profile has never been the thing standing in the way.

Recognising this settles the grant decisions, because the question "does this grant open
a hole" has one answer for every `Bash(<interpreter> <path>)` entry in the file,
including the two already shipped. What is left to decide is what each grant **buys**.

## Decision 1 — `make test`: grant it

**Granted, as `Bash(make test:*)`.**

`AGENTS.md`'s Verification section makes `make test` the repository's verification
command and says plainly: do not conclude tests cannot run locally, and do not defer
verification to CI, without having run it. A lane could not comply — not as a matter of
discipline but structurally, and probe A is the measurement of that. The kit demanded a
verification of every session and denied it to one class of session.

The cost of the gap is not a slow feedback loop; it is that a lane's first verification
is CI, so a lane that breaks the suite learns it only after pushing, and under `dont-ask`
has no round trip left to fix it.

The marginal risk of the grant is nil, per probe C: the profile it joins already carries
the same wedge twice.

### Probe D — the positive construction, and its bound

Profile: `profile-proposed.json` (shipped + the three entries this slice adds).

| # | command | outcome |
|---|---|---|
| 1 | `make test` | ran |
| 2 | `make mutation-test` | **refused** |
| 3 | `uv run scripts/kit_doctor.py --generate-manifest` | ran |
| 4 | `uv run scripts/kit_doctor.py` | ran |

Row 2 is the bound, measured rather than asserted: the runtime matches Bash rules on
token boundaries, so `Bash(make test:*)` admits the `test` target and **not** every
`make` target. `mutation-test` is a different token and is refused. Granting `make test`
is not granting `make`.

Row 1 also settles a question the grant would otherwise raise. `make test`'s recipe
shells out to `uvx ruff` and `uv run --with pytest …`, and neither has an entry in any
list. They ran anyway: the permission check is on the **Bash tool call**, and what the
recipe spawns is that command's own business. So `Bash(make test:*)` alone is sufficient
and no companion `uv`/`uvx` grant is needed. (It is also, read the other way, the same
composition probe B exploited — stated once here rather than twice.)

## Decision 2 — `kit_doctor.py --generate-manifest`: grant it

**Granted, as `Bash(uv run scripts/kit_doctor.py:*)` and
`Bash(uv run scripts/devkit/kit_doctor.py:*)`.**

This is the more damaging of the two gaps, and it fails in a worse place. Editing any
kit-owned file requires the manifest refreshed and committed alongside, or CI fails
deterministically. So a lane given kit-owned work does not merely skip a check — it
produces a **guaranteed-red PR** it cannot make green, and the cockpit must finish it.
`#625` is the worked example. Decision 1's gap costs a lane its local verification;
this one costs the lane its whole result.

Two entries rather than one, because `paths.engines` is the adopter's: `scripts/` here,
`scripts/devkit/` in the layout `.claude/rules/safety-critical-changes.md` supports. That
is exactly how the profile already spells the `pr_watch.py` grant, and matching it is
deliberate — `#606` also proposes templating the engine directory out of the permission
surface, which is a change to how the file is *generated* and applies to every entry in
it at once. Introducing it for one new grant would leave the file half-templated. It
stays `#606`'s open half, on the `.claude/settings.json` surface where the issue raises
it.

**Granted bare rather than scoped to the flag.** `Bash(uv run scripts/kit_doctor.py --generate-manifest:*)`
would have been narrower, and would have denied the natural first move — checking the
manifest before regenerating it — which under `dont-ask` ends the run. Probe D rows 3
and 4 confirm the bare form admits both. Everything `kit_doctor.py` does is within a
lane's legitimate remit, and the narrower spelling buys scoping against no risk this
profile is holding anyway.

One thing the grant does not do: `#464`'s hazard is that
`--generate-manifest` both writes the manifest and prints it, so redirecting its stdout
splices the file. A prefix rule cannot see a redirect, so this grant admits the broken
invocation exactly as it admits the correct one. That belongs in the lane contract, not
in the allow list.

## Decision 3 — `#627`'s `.claude/` guard: what the kit says

Not decidable by a grant. `#627` measured the refusal across `commands/`, `rules/`,
`agents/`, `settings.json` and the bare directory, in two repositories, under two
file-editing tools, in a session that wrote `.agents/`, `docs/` and
`.github/workflows/` — so neither the `Edit(**)` glob nor dot-directories is the
mechanism, and no allow-list entry reaches it. It is the client's own guard.

**Decision: a lane doing kit-owned Claude-adapter work is not a supported case.** The
kit says so in `parallel-headless.md`, beside the profile discussion, which is where
`#627` asks for the answer and where that document already promised `#606` would supply
it. The supported route for a parity change is the one `#625` took by necessity: the
lane does the runtime-neutral half and the Codex adapter, and the `.claude/` half is the
cockpit's. Stated, so the next parity slice does not spend a lane rediscovering it.

This also corrects that document's description of the profile as bounding what a lane can
*do*, which is now wrong in **both** directions and was only ever reported in one:

- there is a class of write the profile cannot authorize (`#627`, `.claude/`), and
- there is a class of execution it authorizes with no rule in any list (probe C).

## Mirroring to Codex

`#606` asks for Claude's policy to be decided before the Codex equivalent is designed,
and the mirror is smaller than it looks. Codex lanes take `--sandbox <policy>` from
`RUNTIME_APPROVAL_POLICIES`, shipped at `read-only`: there is no per-command allow list
on that side, so neither grant has a Codex counterpart to receive. What mirrors is the
doctrine, and it lands in `runtime-parity.md`'s "Command permissions" row:

- The profile is task-scoping, not a security boundary. When a Codex writing policy is
  chosen, `workspace-write` is an OS sandbox and is a *different kind* of mechanism from
  Claude's prefix list — narrower in the way that matters here, since it bounds the
  process rather than the command name. That asymmetry is the parity row's content, not
  a defect to file down.
- The `.claude/` asymmetry is permanent and belongs in the row: a Codex lane edits its
  own adapter directory freely, a Claude lane cannot, so runtime-parity work is not
  symmetrically delegable.

## What this slice does not do

- **It does not close the wedge probe C found.** It names it, and moves the profile's
  description onto what the profile actually delivers. The mechanism that would close it
  is `#631`, filed on the operator's go-ahead with the reproduction and both candidate
  routes; deliberately not built here, because a fix round that also lands a mechanism
  nobody asked for is the trap `safety-critical-changes.md` rule 3 is about.
- **It does not touch the lane contract** (`dev_session.sh print-contract`), which today
  names no verification step and no `.claude/` limitation. Two of this slice's outcomes
  belong there — that a lane may now verify with `make test` before pushing, and that
  `.claude/` is refused so a parity task must arrive already split — and so does
  `#628`'s single-simple-Bash item. `#628` already owns the question of what the
  contract should tell a lane, and the contract lives in a safety-critical engine, so
  the three go there together as one proposal rather than arriving piecemeal in a PR
  about permissions. Routed at wrap-up.
- **It does not template `paths.engines` out of the permission surface.** That is
  `#606`'s other half, on `.claude/settings.json`, along with the `SessionStart` matcher
  and the missing `kit_doctor` check for the permissions block.
- **It changes no adopter's existing profile.** `init.sh` seeds
  `config/claude-lane-settings.json` when absent and never rewrites it, so an installed
  adopter keeps the profile they have and gets these grants only by copying them in.
  `CHANGELOG.md` says so.
