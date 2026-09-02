# cs-toolkit adopter pilot — read-only pass — 2026-09-02

Phase 5's exit test, first half. This is the read-only pass the re-sequenced plan asks
for: `/upgrade` Steps 0 and 1 against the cs-toolkit adopter from a pinned kit clone,
with a stamped record of what the instruments get wrong. **No write was made to the
adopter.** The write pass is a separate slice and needs the adopter operator's
approval.

## What was bound, and where each command ran

Two trees, plus the cockpit's own. Every invocation below used an absolute path or
`git -C`; no `cd` was issued in the session at any point, so no relative path resolved
in the wrong tree.

| role | path | revision |
|---|---|---|
| `$REPO` — the adopter being inspected | `/Users/topi/Coding/in-parallel/cs-toolkit` | `bb9fb1842c4a53d2748412e06782e752803d0185`, `git status --porcelain` printed no rows |
| `$KIT` — the pinned kit clone | `<scratchpad>/kit-pinned` | `3c06e705f3d0646086b14631c86fab61d8f39072` |
| cockpit (this repo, session cwd) | `/Users/topi/Coding/agentic-dev-kit` | `3c06e705f3d0646086b14631c86fab61d8f39072` |

Every reading below was taken on 2026-09-02 against those three revisions. They are
observations of that state and are not to be refreshed in place.

Step 0's shape check: `ls $REPO/config/dev-model.yaml` found the file, so this is an
upgrade rather than an adoption. The adopter declares `kit.version: 2` and
`paths.engines: scripts/devkit`, and `kit-manifest.json` records
`kit_commit: df32eb25a7656b5004c611d1334e8fe8e7de9e09`.

## The instruments disagree, and the workflow sends you to the wrong one first

Step 1 prescribes the adopter's **installed** engine, and offers the kit's copy only
"if `kit_doctor.py` isn't installed yet". Here it is installed and stale, and the two
runs return different verdicts about the same tree:

| run | command | verdict line | exit |
|---|---|---|---|
| A — installed engine | `uv run "$REPO"/scripts/devkit/kit_doctor.py --manifest "$KIT/kit-manifest.json"` | `6 unchanged, 15 differ, 0 missing, 0 unknown`; `⚠ intact for this adoption` | `1` |
| B — pinned kit engine | `uv run "$KIT"/scripts/kit_doctor.py --root "$REPO" --manifest "$KIT/kit-manifest.json"` | `6 unchanged, 15 differ, 1 missing (1 required by an installed engine), 0 unknown`; `✗ NOT intact for this adoption` | `1` |

Run A names no new upstream file. Run B lists eight the baseline mentions neither way,
and fires the drifted-`upgrade.md` banner, the two missing lens definitions, and the
cockpit-grant line — none of which appear in run A at all.

Step 1 does document this under-reporting and prescribes a self-correction: take the
`kit_doctor.py` update, then re-run. **That remedy is a write, so a strictly read-only
pass cannot reach the complete view by the route the step names.** The route that works
read-only is run B, which the step frames as a fallback for an engine that is not
installed. Recommend Step 1 name run B as the read-only route in its own right.

## Instrument misreadings

**1. The `broken, not sized down` verdict is false here, and `#661` has the mechanism
right.** Run B reports:

```text
✗ NOT INSTALLED, and needed by an engine that is — this install is broken, not sized down.
  · scripts/devkit/lib/runtime_adapters.py [engine]  (needed by kit_doctor.py)
```

`grep -c runtime_adapters "$REPO"/scripts/devkit/kit_doctor.py` prints `0`;
the same grep against `"$KIT"/scripts/kit_doctor.py` prints `2`. The file is genuinely
absent, and the engine that is installed does not need it. `scripts/kit_doctor.py:2652`
is the line: `needed_by = [dep for dep in (entry.get("required_by") or []) if
present.get(dep)]` filters on the dependent's **presence**, and the comment beside it
names protecting sized-down adoptions as the reason for that filter. Presence is the
wrong test when the present dependent is an older version whose import set differs;
the test has to be against the installed version's actual requirement.

**2. The lens-definition remedy prescribes an engine the adopter does not have.** Run B
emits:

```text
⚠ .claude/agents/adversarial.md [claude lens=adversarial]: not present
⚠ .claude/agents/correctness.md [claude lens=correctness]: not present
  (… regenerate one with cd <adopter> && mkdir -p .claude/agents &&
   uv run scripts/devkit/panel_prompt.py --root . --lens <name> --agent-definition > …)
```

`find "$REPO" -name panel_prompt.py` returns nothing: the engine is not installed
anywhere in the adopter, and `ls "$REPO"/.claude/agents/` reports the directory does
not exist. So the check is right that the definitions are absent and its remedy cannot
be run. This is `#661`'s shape one check over — written against the kit's dependency
graph rather than against what this adopter installed — and it is a second occurrence
of the same root cause rather than a separate defect. The remedy should either name
`"$KIT"/scripts/panel_prompt.py --root "$REPO"` or say the engine is declined here.

**3. `adopter-owned` is a conservative default, not a finding of authorship.**
`compare_adapters` in `scripts/lib/runtime_adapters.py` recognises exactly one
historical generation — `render_adapter(..., template_version=1)`, plus
`_LEGACY_CODEX_BODIES` for Codex — and its own comment says earlier thick forks are
deliberately not listed. Anything outside that one generation falls through to
`adopter-owned`. On this adopter the classification is nevertheless **correct**:
`diff -u` against the rendered forms shows genuine authored content, not an old render
(see below). Worth stating because the report's wording invites reading a fall-through
as an established fact, and on an adopter pinned further back it would be one.

## Parity findings

**4. `#607` confirmed, and no instrument can see it.** The adopter's lane engines are
repo-owned forks living **outside** `paths.engines`:

| file | adopter | pinned kit |
|---|---|---|
| `scripts/dev_session.sh` | 1019 lines | `scripts/dev_session.sh`, 1073 lines |
| `scripts/reconcile_sessions.sh` | 472 lines | `scripts/reconcile_sessions.sh`, 823 lines |

`wc -l` on each path supplies those. The adopter's `kit-manifest.json` holds 21 file
entries and mentions neither path, and `paths.engines` is `scripts/devkit`, so
`kit_doctor` never inspects either file and `/upgrade` never offers them. `#598` is
**BREAKING** for exactly this pair — the exit `64` unknown-forge hard stop — and
`grep -n 'exit 64'` returns one site in the adopter's `reconcile_sessions.sh` against
two in the kit's. The drift is real, it is in a gate contract, and every instrument
this pilot ran reports the installation as merely sized down.

**5. `#243` confirmed in the field.** Across the eight kit workflow slugs the adopter
binds, per `wc -l` on each adapter path:

| slug | `.claude/commands/<slug>.md` | `.agents/skills/<slug>/SKILL.md` |
|---|---|---|
| adopt | 9 | 18 |
| parallel | 91 | 19 |
| post-merge-systemize | 260 | absent |
| pr-watch | 50 | 13 |
| session-start | 240 | 13 |
| triage-friction-log | 335 | absent |
| upgrade | 8 | 18 |
| wrap-up | 7 | 26 |

Summing those columns with `wc -l` over the same paths prints `claude total=1000
codex total=107`. Two workflows have no Codex binding at all, and the adapter report
classifies the Codex `post-merge-systemize` and `triage-friction-log` skills as
`missing — install the rendered adapter`.

**6. The adopter invented the mechanism the kit lacks, and applied it once.**
cs-toolkit made `wrap-up` runtime-neutral by pointing **both** adapters at a repo-local
`docs/developer/wrap-up-local.md`. Its Codex skill states the reason outright:

> Without that, the same session wrapped up here gets a weaker accuracy standard than
> the same session wrapped up on Claude — which is the concrete shape of the divergence
> this conversion exists to end.

The pattern is applied to `wrap-up` alone. `session-start` carries a 240-line
`## cs-toolkit appendix` in the Claude command whose opening states it extends the
shared workflow and never replaces it — remote-session detection, and a rule to read the
narrative files against `origin/main` rather than the working tree. That appendix records
its own occurrence: a session on 2026-08-10 opened on a feature branch, missed a handoff
block that had already merged, and filed a duplicate ticket. The Codex
`session-start` skill is 13 lines and `grep -i` for `appendix`, `.claude/commands`,
`origin/main` and `Darwin` in it returns nothing. **A Codex session at this adopter runs
`$session-start` without the rule whose absence has already cost that repo a duplicate
ticket.** The same asymmetry stands for `pr-watch`, `parallel`,
`post-merge-systemize` and `triage-friction-log`.

The kit ships no convention for a repo-local, runtime-neutral appendix. `AGENTS.md`
tells adopters that doctrine reaching every runtime does not belong in `.claude/rules/`,
and offers no surface where it does belong. cs-toolkit's `<workflow>-local.md` is that
surface, invented downstream, and is the strongest candidate this pilot found for
promotion into the kit.

**7. `#662` confirmed at the adopter.** Among the eight files run B reports as added to
the kit since the baseline, and which `/upgrade` would offer:

```text
scripts/devkit/verify_live_validation_bundle.py
scripts/devkit/tests/test_live_validation_bundle.py
docs/agentic-dev-kit/live-validation-evidence.md
```

Nothing in the adopter's tree is verifiable by any of them. The sprint review predicted
this from the manifest; the pilot observes it as an offer a real adopter would receive.

## What the adopter would receive

`git diff df32eb2..3c06e70 -- CHANGELOG.md` in the cockpit lists the entries added
since the recorded pin: `#580`, `#588`, `#590`, `#593`, `#595`, `#596`, `#598`, `#599`,
`#609`, `#611`, `#614`, `#623`, `#632`, `#635`, `#637`, `#639`, `#649`, `#651`, `#653`,
`#655`, `#659`. `git rev-list --count df32eb2..3c06e70` prints `54`. `#598` is the one
that breaks a contract the adopter has forked outside the kit's view.

## Residue

- The two lens definitions are absent and `.claude/agents/` does not exist, so the
  adopter cannot run a configured fallback panel. Blocked behind finding 2.
- Run B's cockpit-grant line reports no `permissions.allow` rule reaching
  `scripts/devkit/pr_watch.py`; the adopter's `.claude/settings.json` holds 12 allow
  rules and none matches. Informational by design, and true here.
- `docs/agentic-dev-kit/workflows/upgrade.md` is `STALE` at the adopter, so an upgrade
  run there would execute Steps 0 through 3 from the older copy. Following `$KIT`'s copy
  is what this pass did.

## Next

The write pass, on the adopter operator's approval, and not before. Findings 1 and 2 are
kit-side and can land before it; findings 4 and 6 are the two that decide what the write
pass has to do.
