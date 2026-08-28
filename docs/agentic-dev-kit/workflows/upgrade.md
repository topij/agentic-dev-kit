# Upgrade

Upgrade this repo's agentic-dev-kit installation. Runs on a branch. Two of its file
replacements are unconditional and named here rather than implied — Step 2 overwrites
`init.sh` and `docs/templates/*.tmpl` with the fetched kit's copies, because refreshing the
installer is the point of the step. **Everything else is gated**: `init.sh --no-clobber` for
the seeded docs, and your per-file decision in Step 3 for the engines.

**Do not simplify that back to a blanket "non-destructive".** It said "never replaces a file
without knowing it is safe to replace" for as long as Step 2 ran `init.sh` bare, which
destroyed exactly the file it promised to protect (`#330`). A reassurance at the top of a
workflow is executed prose — it suppresses the check further down. The carve-out above is
deliberate for the same reason: an adopter who edited `init.sh` loses that edit here.

**What that costs changed with `#362`, and this sentence used to say otherwise.** It read
"`kit-manifest.json` does not track the file, so `kit_doctor` cannot report the drift
either" — true when written, false since `#362` added `init.sh` to `KIT_OWNED` and to the
manifest. The correction is kept visible rather than swapped in silently, because the
instruction it produced was *don't bother looking*, which is the opposite of what `#360`
was closed to make possible. So: **run Step 1's `kit_doctor` before Step 2 overwrites
anything** — a locally-edited installer shows up there as `LOCALLY EDITED` and an
out-of-date one as `STALE`, which is the difference between an edit you are about to lose
and a version you are meant to take. The unconditional `cp` itself is unchanged and
`#339` stays open for it.

> **The invariant this rests on.** Engines are **kit-owned**; config is **adopter-owned**.
> Everything project-specific — paths, tracker, review-bot markers, CI policy, model
> tiers — lives in `config/dev-model.yaml`, so an engine should never need editing to
> adopt it. That is what makes an upgrade a file copy instead of a manual merge. If this
> run finds engines you had to edit, that is a **kit bug**: report it rather than
> carrying the patch forward.

## Step 0 — Establish what shape this repo is in

Four shapes exist in the wild and they need different handling. Determine which:

```bash
ls config/dev-model.yaml 2>/dev/null && echo "has config" || echo "NO CONFIG"
```

- **No `config/dev-model.yaml`** → this repo predates the config surface entirely (a kit
  *ancestor*, or a partial hand-install). **Stop and run `/adopt` instead** — there is no
  schema to migrate from. Say so plainly rather than guessing a config into existence.
- **Config present** → continue. `kit.version` tells you the schema generation; its
  absence means v1 (pre-`runtime:`, pre-`models.tiers`).

Also fetch the kit you are upgrading *to*, if it isn't already local:

```bash
git clone --depth 1 https://github.com/topij/agentic-dev-kit /tmp/agentic-dev-kit
```

Everything below copies **from** that checkout **into** this repo — **two trees, and
from here every write must name which one.** Bind both roots now, before the first
write, and use them for the rest of the workflow:

```bash
REPO="$(git rev-parse --show-toplevel)"   # the repo being upgraded
KIT=/tmp/agentic-dev-kit                  # the kit you are upgrading TO
echo "REPO=$REPO"; echo "KIT=$KIT"; echo "pwd=$(pwd)"
```

**Check that output before continuing.** `$REPO` must be the repo you meant to upgrade,
and `pwd` must be inside it. This is the assertion, and it belongs *before* the first
write — after it, it is a post-mortem.

The hazard is that a `cd` into `$KIT` — to inspect the fetched kit, to read a file —
**outlives the command that made it**, and every relative path afterwards resolves in
the clone. Two sessions lost time to exactly this on 2026-08-09, and neither recognised
it: one had `cp` and `./init.sh` land in the verification clone and read it as filesystem
corruption; the other ran greps in the wrong tree and got a startling wrong answer it
nearly believed. The failure mimics a broken tool rather than a wrong directory, which
is why the guard has to be structural rather than attentive (`#399`).

When you verify a copy landed, **hash it at the destination** —
`shasum -a 256 "$REPO/<path>"` — rather than reading `git status` from wherever the
shell is. In the first occurrence above, the destination hash is what would have
revealed it, and `git status` is what concealed it.

**This binds reads and invocations, not only writes** — which is why every
`<engine-dir>/…` command below is spelled `"$REPO"/<engine-dir>/…` rather than
relative. `paths.engines` is a path *relative to the repo root*, and Step 0 pins `pwd`
to be somewhere **inside** `$REPO`, not at its top — so a relative invocation resolves
against wherever the shell happens to be. Executed from `docs/` in this repo:

```text
$ uv run scripts/kit_doctor.py --manifest "$KIT/kit-manifest.json"
error: Failed to spawn: `scripts/kit_doctor.py`
```

That one is loud. The `--root` form is not: `--root .` from a subdirectory reports
`dev-model config not found: <subdir>/config/dev-model.yaml` and prescribes
*"a repo with no config/dev-model.yaml predates the config surface entirely — adopt it
with the /adopt skill rather than upgrading"* — sending you to Step 0's stop-and-adopt
branch for a repo that is fully adopted. A wrong `pwd` is not in the differential that
error invites you to consider.

Anchoring the **script path** is sufficient here and no `cd` is needed: `kitconfig`'s
`repo_root()` walks up from `Path(__file__)`, not from the working directory, so an
engine reached by an absolute path finds its own repo root wherever you invoke it from.
`--root` is the exception, because it is an explicit override that bypasses that walk —
which is why it takes `"$REPO"` above rather than `.`.

## Step 1 — Diff the installation (read-only)

```bash
uv run "${REPO:?REPO is not set — re-run Step 0}"/<engine-dir>/kit_doctor.py --manifest /tmp/agentic-dev-kit/kit-manifest.json
```

Read `<engine-dir>` from `paths.engines`. If `kit_doctor.py` isn't installed yet, run the
kit's copy against this repo: `uv run /tmp/agentic-dev-kit/scripts/kit_doctor.py --root
"${REPO:?REPO is not set — re-run Step 0}" --manifest /tmp/agentic-dev-kit/kit-manifest.json`.

The report gives you, per kit-owned file: `unchanged` / `differs` /
`unknown-version` / `missing-required`, and — for an absent file — one of `declined` /
`removed` / `new-upstream` where this repo has a **declared install set**, or the older
undifferentiated `missing` where it does not. Plus four installation-level checks.
**Read all four** — each is a silent failure mode:

- **config schema version** — unversioned or behind means migrations are pending.
- **`paths.engines` resolves to a directory that actually holds engines.** A `✗` here is
  the live breakage where every workflow's `<engine-dir>/…` reference points at nothing.
  Nothing else validates this value, so nothing else would have told you.
- **pre-push hook installed** — a shipped-but-uninstalled hook binds nothing.
- **narrative docs and entry points rendered** — a file whose **first line opens an HTML
  comment beginning with** `devkit-template: unrendered` (a narrative skeleton) or
  `devkit-source: kit-own` (a root `AGENTS.md` / `CLAUDE.md` that is still the kit's own)
  means the adoption never completed its seeding step. A file that merely quotes a marker
  — further down, or after other words inside a line-1 comment — is in use and is reported
  as such.

**A `0 missing` (or a `missing`/`new-upstream` count that leaves a real file out) is
not evidence there is nothing new — it is a property of what this run of `kit_doctor`
knows how to look for, not of the kit.** `inspect()` walks the `KIT_OWNED` tuple
compiled into the **running** script — your installed `<engine-dir>/kit_doctor.py` —
and consults `--manifest` only to look up a hash for a path that tuple already names.
A file the kit gained after your installed copy was built sits outside that tuple, so
this first run does not count it, name it, or hint at it anywhere in the report. It is
self-correcting: the same run reports `<engine-dir>/kit_doctor.py` itself as `differs`
(or `STALE`), and taking that update in Step 3 is what makes the new file visible.
**Take that engine update first, then re-run this command, before scoping anything
from a first report.** `CHANGELOG.md`'s `#553` entry is a worked instance: the
workflow doc it added was invisible to a pre-upgrade `kit_doctor` for this exact
reason, and named nowhere until `kit_doctor.py` itself was refreshed.

Then classify the runtime adapters with the **fetched kit's** renderer, not the
installed engine's older idea of their shape:

```bash
uv run "${KIT:?KIT is not set — re-run Step 0}"/scripts/kit_doctor.py \
  --root "${REPO:?REPO is not set — re-run Step 0}" \
  --adapter-report --adapter-source "${KIT:?KIT is not set — re-run Step 0}"
```

This comparison is deliberately outside `KIT_OWNED` and never changes the drift
gate. `kit-current` is byte-identical to the current rendered form; `kit-stale`
matches an earlier rendered form and can be refreshed without losing authored
behavior; `missing` can be installed; `adopter-owned` matches no known rendered
form, so report it and leave it unchanged. The source kit's own adapters must first
equal what its renderer produces, or the command refuses: a broken generator cannot
classify an adopter by comparing it with itself.

**A related risk sits one level up, in this very file, and whether the run above even
catches it depends on when your installed copy was built.** `upgrade.md` has been
tracked in `KIT_OWNED` since `#337`. If your installed `<engine-dir>/kit_doctor.py`
postdates that commit, an out-of-date `upgrade.md` is not invisible: the run above
reports it `differs`/`STALE` like any other tracked file. If your installed copy
predates `#337`, it is invisible for exactly the reason the paragraph above
describes. **Either way, a report is not a fix.** Step 4 is where this file is
actually refreshed, and Steps 2–3 run before Step 4 does — on whatever copy is on
disk right now, whatever this run just reported about it (`#544` anchored every
engine invocation here to `$REPO`; a repo upgrading from before it runs Steps 2–3
against the unanchored prose regardless of what Step 1 said). Confirm now, while
this step is still read-only: diff
`"${KIT:?KIT is not set — re-run Step 0}/docs/agentic-dev-kit/workflows/upgrade.md"`
against
`"${REPO:?REPO is not set — re-run Step 0}/docs/agentic-dev-kit/workflows/upgrade.md"`;
if they differ, finish this upgrade following `$KIT`'s copy.

**This paragraph cannot be the thing that saves you, and other surfaces carry it for
that reason.** A reader whose copy is out of date is reading the out-of-date copy — so an
instruction written *here* about *this file* reaches everyone except the person who needs
it. The remedy has to come from outside: `kit_doctor` gives this file its own line at the
top of the report rather than leaving it in the drift list with everything else, and the
runtime adapters (`.claude/commands/upgrade.md`, `.agents/skills/upgrade/SKILL.md`) say
to re-read this workflow from the clone before Step 2. Neither is a complete answer
alone, and they fail in opposite directions, which is why each exists: the adapter is
the only surface read before *any* of this, but it is adopter-owned and Step 4 keeps
your version, so a kit fix to it never reaches a repo already adopted; the engine does
reach every upgrade, but only from the *next* one — the copy running Step 1 today is the
copy you installed last time. (An operator who takes the engine update inside Step 1 and
re-runs, as the paragraph above prescribes, gets it in this run — but that prescription
is itself in this file, so it inherits the same problem.) **Do not delete either as a
duplicate of this paragraph** — they are the copies a stale reader can reach, and this is
the one they cannot (`#577`).

**What `differs` splits into depends on whether this repo has a *trusted* baseline.** A
baseline is `kit-manifest.json` here recording what *this repo installed*, written by
`--record-install` at the end of Step 4. Trusted means it carries a `kit_commit` key —
that key is written only by `--record-install`, so its presence is what distinguishes a
record of an install from a manifest that was merely copied in. With one, the report
states a cause as fact:

- **`STALE`** — byte-identical to what was installed here, so nothing was edited.
  Replace it; nothing local is lost.
- **`LOCALLY EDITED`** — changed here since install, and the kit's copy never moved.
- **`STALE and LOCALLY EDITED`** — both. The only state that can lose work.

Without a trusted one — **including an existing `kit-manifest.json` that has no
`kit_commit`**, which is every repo adopted before this field existed — it falls back to
`differs` and **does not claim a cause**: a hash mismatch alone cannot distinguish
"older kit version" from "hand-edited", and the schema-version signal it used to narrow
by tracks the *config schema*, not file contents, so it was wrong for every kit change
that did not bump the schema (kit `#51`). Confirm with an actual diff in Step 3.

A `baseline: none recorded` line here is expected on a first upgrade and is not an error;
Step 4 writes the baseline. Do **not** run `--record-install` at this point — it writes a
file, and everything before Step 2 must stay read-only.

### Then read what the new files will *do* differently

`kit_doctor` answers "did this drift". It never answers "what does the new one do
differently", and Step 3 below hands you a per-file verdict without that second answer
attached. `CHANGELOG.md` in the kit checkout is where it lives — the observable changes
only, no rationale — and **this** is the step that can narrow it to *your* answer, because
the report you just ran knows which kit commit this repo installed from.

Read it now, before Step 3 copies anything. Skipping it does not fail the upgrade; it
defers the cost to whenever your own tests go red after a file copy, with no way to tell
"the kit broke my repo" from "my repo pinned the old contract". Distinguishing those was
the bulk of one adopter's refresh session, for two changes that were both landing
correctly (`#430`).

**The Step 0 clone is `--depth 1`, so it has no history to range over.** Deepen it first.
Skip this and the guard below cannot distinguish your shallow clone from a baseline that
was never in this history, so it routes you to the degraded path and you read a partial
answer as a complete one:

```bash
git -C "${KIT:?KIT is not set — re-run Step 0}" fetch --unshallow 2>/dev/null ||
  git -C "${KIT:?KIT is not set — re-run Step 0}" fetch --depth=1000
```

Then resolve the baseline and the PRs that landed after it. A squash merge on the kit
ordinarily carries its PR number as a trailing `(#NNN)`, and every changelog entry is
headed by the PR that made the change — so those numbers are the index.

**Ordinarily, not always, and the gap is silent.** A subject ending any other way —
several references (`(#37, #146)`), text inside the parens (`(#134 cause 1)`), a
`Merge pull request` subject, or a commit that never went through a PR — yields no number
and is simply skipped. That looks exactly like "this commit changed nothing observable",
which is the same fail-open shape as the empty baseline below.

Non-conforming subjects are a real part of this repo's early history and absent from its
recent history. Count them for yourself rather than trusting a figure written here, which
goes stale the moment another commit lands — and count against `main`, since an unmerged
branch's own commits have no PR number yet and would read as a fault:

```bash
git -C "${KIT:?KIT is not set — re-run Step 0}" log --format='%s' origin/main | grep -cvE '\(#[0-9]+\)$'
```

So the count below is a tripwire rather than a formality — if it fires, the index is
incomplete and the top of `CHANGELOG.md` is the fallback:

```bash
BASELINE="$(uv run "${REPO:?REPO is not set — re-run Step 0}"/<engine-dir>/kit_doctor.py --manifest "${KIT:?KIT is not set — re-run Step 0}/kit-manifest.json" --json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin).get("baseline_kit_commit") or "")')"
echo "baseline=${BASELINE:-NONE}"
if [ -z "$BASELINE" ] ||
   ! git -C "${KIT:?KIT is not set — re-run Step 0}" merge-base --is-ancestor "$BASELINE" HEAD 2>/dev/null; then
  echo "no usable install provenance — take the degraded path below"
else
  COUNT="$(git -C "${KIT:?KIT is not set — re-run Step 0}" rev-list --count "$BASELINE..HEAD")"
  SUBJECTS="$(git -C "${KIT:?KIT is not set — re-run Step 0}" log --format='%s' "$BASELINE..HEAD")"
  if [ "$COUNT" -gt 0 ]; then
    INDEXED="$(printf '%s\n' "$SUBJECTS" | grep -cE '\(#[0-9]+\)$' || true)"
    UNINDEXED=$(( COUNT - INDEXED ))
    [ "$UNINDEXED" -gt 0 ] && echo "⚠ $UNINDEXED commit(s) in range carry no trailing (#NNN);
   they are NOT indexed below — read CHANGELOG.md from the top as well"
    printf '%s\n' "$SUBJECTS" | grep -oE '\(#[0-9]+\)$' | tr -d '()#' |
      while read -r pr; do
        awk -v pr="$pr" '/^## /{p = ($2 == "#" pr)} p' "${KIT:?KIT is not set — re-run Step 0}/CHANGELOG.md"
      done
  else
    echo "up to date — no commits between your baseline and the kit's HEAD"
  fi
fi
```

**The `if` is not decoration.** An empty `$BASELINE` interpolated into
`"$BASELINE..HEAD"` gives `..HEAD`, which git reads as `HEAD..HEAD` and prints nothing at
all — so the one case that knows least about your repo is the one that renders as "no
observable changes since your baseline". That is the fail-open direction, and it is
silent. A *non-empty* baseline that `$KIT` cannot resolve fails the other way —
`fatal: Invalid revision range` — which is loud but still never reaches the degraded path
below, so the reader gets a git error instead of the procedure written for exactly their
case. `merge-base --is-ancestor` covers both, and covers the baseline that resolves but
sits on a history this checkout does not descend from.

The `-z` test in front of it is deliberate redundancy, not a second guard: `merge-base
--is-ancestor "" HEAD` already fails, so removing `-z` changes no outcome here. It is
written out because that behaviour is git's, not this procedure's, and a guard whose
correctness rests on how another tool treats an empty argument is one silent upstream
change from being wrong. Nothing downstream distinguishes the two forms — the tests
cannot, because both land on the same degraded path.

**Deepen before you guard — the order is the whole point.** `--is-ancestor` cannot tell
"the clone is shallow" from "that commit is not in this history", because in a `--depth 1`
clone the object is simply absent, so it exits **128** with a `fatal:` message, where a
commit that is present but off this history exits **1** silently. The `!` is what
collapses those two into one degraded-path decision, since it negates any non-zero exit;
the `2>/dev/null` beside it only suppresses the message, which would otherwise read as a
procedure that broke rather than one that took its documented fallback. Run the
guard against an undeepened clone and every upgrade quietly takes the degraded path, which
is strictly worse than the error it replaced: an error stops you, a degraded read looks
like an answer.

A PR that produced no output has no entry, and a PR with no entry made no observable
change. That is the file's contract rather than an omission to chase.

**`baseline_kit_commit` empty is a real, supported value — degrade, do not guess.** Three
causes reach it and nothing here can tell them apart: `--record-install` never ran
(`baseline: none recorded`); it ran without `--from-kit`, so the baseline is trusted but
carries no provenance (`recorded, install provenance unknown`); or the recorded value is
not a string, which `kit_doctor` normalizes away rather than aborting the report over.
There is no range to compute, so:

- Read `$KIT/CHANGELOG.md` from the top instead, and treat every `BREAKING` line as
  applying to you until you can show otherwise. It is newest-first and short by
  construction — this is minutes, not the session `#430` describes.
- If you know roughly when this repo last upgraded, bound it by date instead:
  `git -C "$KIT" log --since=<date> --format='%s'`, then index as above.
- Either way, **Step 4's `--record-install --from-kit "$KIT"` is what stops the next
  upgrade paying this** — the same step, and the same `kit_commit` key, that the `STALE`
  / `LOCALLY EDITED` split above already depends on.

A baseline **older than the changelog itself** also finds nothing, and that is not a fault
either: the file records nothing before the PR it starts at, and says so in its own
header.

## Step 2 — Branch, refresh the migrator, then migrate

**Branch first.** Everything from here mutates the repo — config, hooks, rendered
docs — so the "runs on a branch" guarantee has to be established *before* the first
mutation, not before the file copies in Step 3:

```bash
cd "$REPO" || exit 1
git checkout -b chore/kit-upgrade
```

**Then refresh `init.sh` itself before running it.** This is the step that is easy to get
backwards: the repo's existing `init.sh` is the *old* one, and it does not contain the new
schema migrations — so running it would report success while silently applying nothing new.
Take the fetched kit's copy first:

```bash
cd "$REPO" || exit 1                              # every write below lands here, not in $KIT
cp "${KIT:?KIT is not set — re-run Step 0}/init.sh" "${REPO:?REPO is not set — re-run Step 0}/init.sh"
chmod +x "${REPO:?REPO is not set — re-run Step 0}/init.sh"  # the kit ships it 100755; a copy can lose the bit
mkdir -p "${REPO:?REPO is not set — re-run Step 0}/docs/templates"
_gate_failed=0
for _tmpl in "${KIT:?KIT is not set — re-run Step 0}"/docs/templates/*.tmpl; do
  _rel="docs/templates/$(basename "$_tmpl")"
  python3 -c 'import json,pathlib,sys
b = pathlib.Path(sys.argv[1]) / "kit-manifest.json"
try:
    d = json.loads(b.read_text(encoding="utf-8"))
except FileNotFoundError:
    if b.is_symlink():           # present but dangling: unreadable, not absent
        print(f"{b}: dangling symlink", file=sys.stderr)
        sys.exit(2)
    sys.exit(1)                  # genuinely absent: no declared scope, copy
except Exception as exc:         # ANY other read/parse failure: refuse, do not guess
    print(f"{b}: {type(exc).__name__}: {exc}", file=sys.stderr)
    sys.exit(2)
if not isinstance(d, dict):
    print(f"{b}: top-level value is {type(d).__name__}, not an object", file=sys.stderr)
    sys.exit(2)
if "kit_commit" not in d:
    sys.exit(1)                  # not a --record-install baseline: no declared scope
if "not_installed" not in d:     # PARTIAL record, not a broken one — see below
    sys.exit(3)
declared, files = d["not_installed"], d.get("files")
if not isinstance(declared, list) or not isinstance(files, dict):
    print(f"{b}: kit_commit is present but the declared scope is unreadable "
          f"(not_installed={type(declared).__name__}, files={type(files).__name__})",
          file=sys.stderr)
    sys.exit(2)                  # a baseline that cannot state its scope is not a licence
sys.exit(0 if sys.argv[2] in declared else 1)' \
    "${REPO:?REPO is not set — re-run Step 0}" "$_rel" && _verdict=0 || _verdict=$?
  case "$_verdict" in
    0) echo "declined (recorded in not_installed) — not copied: $_rel" ;;
    1) cp "$_tmpl" "${REPO:?REPO is not set — re-run Step 0}/$_rel" ;;
    3) echo "no declared scope recorded — not copied: $_rel"; _partial=1 ;;
    *) echo "STOP: $REPO/kit-manifest.json is not a readable manifest, so the declared set is unknown. Copied nothing." >&2
       _gate_failed=1; break ;;
  esac
done
if [ "${_partial:-0}" -ne 0 ]; then
  echo "note: the baseline carries kit_commit but no not_installed key, so it declares no" >&2
  echo "      scope and the templates above were left alone rather than copied over" >&2
  echo "      declines that cannot be read. This is a PARTIAL record, not a broken one:" >&2
  echo "      one kit-owned file that does not byte-match the source kit suppresses the" >&2
  echo "      whole key (see Step 5, and kit #388). Reconcile the paths Step 4 named and" >&2
  echo "      re-run this block if you want the templates refreshed." >&2
fi
if [ "$_gate_failed" -ne 0 ]; then
  echo "Not running init.sh. Fix kit-manifest.json, then re-run this block." >&2
else
  "${REPO:?REPO is not set — re-run Step 0}/init.sh" --no-clobber
fi
```

The refreshed migrator also owns the additive `parallel:` launcher block. It preserves
each existing flat value and adds only missing `codex_headless_command`,
`descriptor_ttl_seconds`, `observation_timeout_seconds`, and
`termination_grace_seconds` keys, the per-runtime `*_transport` declarations, and the
per-runtime approval policy — `codex_approval_policy`, `claude_approval_policy`, and
`claude_settings_profile`. A same-named key nested under another child is not a
flat launcher key and does not suppress the shipped default. The command is an argv
sequence consumed without a shell; the lifetime, observation bound, and termination
grace must remain positive integers for descriptor issuance and launch; each
approval policy must stay inside the wrapper's vocabulary (Codex `read-only` /
`workspace-write`, Claude `dont-ask` / `accept-edits`) — an unrestricted spelling
refuses at launch. The same run seeds the Claude lane settings profile at the path
`claude_settings_profile` names when no file is there (`seeded <path>`), and never
rewrites one that exists: the profile is adopter-owned lane policy, outside the
manifest, so an upgrade cannot replace your allow-list; diff it against the kit's
`config/claude-lane-settings.json` yourself when you want the shipped entries.

The refreshed migrator owns the additive `triage:` block. It inserts the complete flat
block when absent and adds only missing keys to a partial block, preserving existing
values, indentation, and trailing comments. Ambiguous top-level or child-key YAML stops
before any migration write. The shell-only parser also stops on multi-line flow
collections inside init-owned sections and on a sequence where an owned mapping is
required; normalize prompted-section child keys to the shipped two-space indentation,
keep a partial `triage` flat map at one consistent indentation, and keep flow or quoted
values complete on the same line as their keys. Prompted values also reject YAML tags,
anchors, aliases, block scalars, and block children. Partial-`triage` string fields also
reject double-quoted backslash escapes. Normalize `review.bots` and
`systemize.operator_logins` to complete same-line flow sequences; normalize every other
prompted value to a same-line scalar, never a flow mapping. Quote a string whose plain
spelling YAML could resolve as a non-string; string fields must be non-empty, and
`triage.pr_draft` must be the plain boolean `true` or `false`. Block YAML on other fields can still be refused
when its continuation resembles migrator-owned structure; normalize any refused value
to an ordinary same-line form. Do not retain or create a separate
`config/friction-triage.yaml`: `paths`, `tracker`, `notify`, `state`, `vcs`, and
`models` remain the authoritative shared sections. After this step, verify that
`triage.state_path` and `triage.gate_path` separate live/test mode, the recovery-bundle
pattern carries mode and gate-digest placeholders, and the frozen-inbox and report
patterns carry mode, date, and session placeholders.

The older Claude and Codex triage adapters carried approval and notification policy
outside the shared workflow. When the selected changelog entry names this migration,
replace both adapters with the refreshed thin bindings even though Step 3 normally
retains adopter-owned adapters. Keeping either old adapter leaves runtime-dependent gate
semantics around the new shared state and exact-payload contract.

Every path above is absolute or `$REPO`-anchored, per **Working across two trees** in
[`AGENTS.md`](../../../AGENTS.md) — the rule this workflow binds by setting `$REPO` and
`$KIT` in Step 0 above — including the manifest the gate reads, which is the adopter's and
not the kit's. The
`cd "$REPO"` is still required and is not redundant with them: `init.sh` resolves the
config and the templates **against the working directory**, not against its own location
(the same reason running `$KIT/init.sh` in place of the copy is not equivalent, below). So
the `cd` sets what `init.sh` reads and the absolute paths set where everything else lands
— and if the `cd` fails, the run stops rather than writing into whatever tree the shell
was in.

**The template copy is gated on the declared install set, and that gate is the
difference between a refresh and a silent reversal.** A path listed in the baseline's
`not_installed` is a **decision** the adopter recorded. Copying it in anyway is invisible
at the time — `cp` says nothing, and `kit_doctor`'s `missing` count goes *down*, which
reads as an improvement — and Step 4's `--record-install` then derives the installed set
from what is on disk and writes the reversal in as fact. A repo that declined six
templates comes out the other side declaring twenty installed files where it declared
twenty-six, with nothing anywhere recording that a decision was reversed. `#398`, found by
an adopter who spotted the unconditional instruction and declined to follow it.

**A manifest that is present but not readable as a manifest stops the step rather than
falling back to copying.** Absent and corrupt are different states and only the first is
safe to treat as "no declared scope": a corrupt manifest may well hold declines nobody can
now read, and copying over them is the very reversal this gate exists to prevent, reached
by another route. So `FileNotFoundError` means no baseline and every template is copied,
while anything else refuses, names the file on stderr, and copies nothing.

**The shape checks mirror `kit_doctor.py`'s `_declared_scope` deliberately** — the same
`not_installed`-is-a-list test and the same companion `files`-is-a-dict test (a scope
claim needs both halves). That function is where this repo already settled what a readable
declared scope is, and it carries its own parametrized regression test. **Two deliberate
differences:**

- **Direction of failure.** `_declared_scope` returns `None` and its caller reports
  "cannot judge", because it is a read-only diagnostic. Here the same condition must
  REFUSE, because the alternative is copying over declines nobody can read.
- **No string filter over the list.** `_declared_scope` needs one because it returns a
  set other code consumes; a membership test does not — `x in [5, "x"]` and
  `x in ["x"]` agree for every input. Carrying it here would be a guard that no
  mutation can kill, which is the shape this repo keeps finding as "a property named in
  a comment and pinned by nothing". It was written, mutation-tested, found inert, and
  removed.

**Each of these checks was added after the previous version was shown to fall through to
copying** — four rounds of it, which is the argument for mirroring a settled
implementation rather than continuing to invent one:

- a read or parse error — **any** exception, not an enumerated set. The first form let
  `JSONDecodeError` escape as a traceback, once per template, and copied anyway; the
  second caught `(OSError, ValueError)` and left the same hole one type over, since
  `RecursionError` is a `RuntimeError` and a deeply-nested array reaches it (verified at
  depth 200,000 on CPython 3.14.6). **Two enumerations, two holes, same shape** — so the
  enumeration is gone rather than extended a third time. The `try` body is one
  `read_text` + `json.loads`, so `except Exception` is precise here rather than broad:
  there is no other statement in it whose failure could be masked;
- a top-level value that parses but is not an object — `null`, `42`, `true` raise
  `TypeError` on the membership test and exit 1 (copy), while `[…]` and `"…"` evaluate
  the test to `False` and exit 1 (copy) with no error at all, which is the quieter and
  worse half;
- the refusal has to stop **the workflow**, not just the loop. `break` leaves the
  `for` loop and the next line still runs `init.sh` — printing "Copied nothing" and then
  proceeding past the point the prose calls a hard stop. `_gate_failed` is what makes the
  stop real;
- a well-formed object is not a readable scope. `{"kit_commit": …, "not_installed": 5}`
  raised `TypeError` on the membership test and exited 1 (copy); a **string** there was
  worse than that, because `in` on a string is a SUBSTRING test — no error, and a
  comma-joined value could answer *true* for a path nobody declined;
- **an ABSENT `not_installed` is a partial record, not a broken one, and conflating the
  two aborts a routine upgrade.** `kit_doctor.py`'s `record_install_manifest` omits the
  key entirely — not `[]` — whenever any kit-owned path is `unverified`, writes the
  baseline anyway, and exits 1 to say the record is partial. Step 5 below already calls
  a deliberately-kept local patch "the usual way in" to that state. An earlier version of
  this gate refused it and suppressed `init.sh` with it, so an adopter carrying one patch
  found the whole config migration blocked, with a STOP message whose suggested remedy
  did not address the cause — and whose only obvious workaround, deleting the manifest,
  reopens `#398`. It now skips the copies (the declines genuinely cannot be read), says
  why, names `#388`, and **still runs `init.sh`**;
- and `FileNotFoundError` alone does not mean *absent*. A **dangling symlink** at that
  path raises it too, so the one shape the taxonomy treats as safe was also catching a
  present-but-unreadable manifest. `is_symlink()` separates them — it does not follow the
  link, so it stays true exactly where `exists()` has gone false. `#303` records the same
  shape one file over, where a dangling symlink at `.codex/hooks.json` defeated three
  rounds of guards.

All four came out of the fallback review panel, two of them as HIGHs, each in the previous
round's remediation.

The `kit_commit` test is what distinguishes a real baseline from the kit's own shipped
manifest sitting at the same path (the same distinction Step 1 draws above): a manifest
without it has no `not_installed` to honour, so nothing is gated and every template is
copied — which is the correct behaviour for a repo that never declared a scope.

If the operator wants a declined template *now*, that is a decision to state and record,
not a side effect of a refresh: copy it by hand and say so in the PR, so Step 4 records a
transition someone chose.

**`--no-clobber` is not optional here, and it is the one flag that changes what this step
can destroy.** Bare `init.sh` seeds two classes of target: one that is *absent*, and one
that *exists carrying a kit marker on line 1*. The second class is where an adopter's own
work lives — a repo that took the pre-`#288` `cp -r` quickstart got marked skeletons, and
months of doctrine written into one does not remove the marker. `README.md` documents
re-running `init.sh` as the supported upgrade path, so the exposed party is a long-running
adopter, not a new one. Measured in two `git init` sandboxes against the merged `init.sh`:

| target state | bare `./init.sh` | `./init.sh --no-clobber` |
|---|---|---|
| **absent** | `seeded AGENTS.md` | `seeded AGENTS.md` — unchanged by the flag |
| marked, never edited | rendered | `left untouched (--no-clobber): AGENTS.md`, byte-identical |
| **marked, edited by the adopter** | `seeded AGENTS.md` — **content gone, no backup** | declined, byte-identical |

The first row is the one to read before worrying that this weakens the step: `--no-clobber`
narrows seeding to genuinely-absent targets, and absent is precisely what the paragraph
below needs it to still do. A partially-adopted repo missing `AGENTS.md` or `CLAUDE.md`
still receives it.

**What it costs, stated plainly:** a marked file that was *never* edited — a pristine
skeleton — now stays unrendered where it used to be rendered. That is a real regression and
it is why this is worth stating rather than burying. It is also the loudest line in the run:
each decline is printed per-file *and* again in an end-of-run summary, so it cannot pass
unnoticed. Resolve a file it names in one of two ways, both of which the operator owns:

- **Keep the content** → delete line 1. The file is then yours and nothing seeds it again.
- **Take the kit's version** → delete the file and re-run. It is now absent, so it seeds.

Do neither on the operator's behalf. The whole point of the flag is that the choice between
those two is not `init.sh`'s to make, and it is not this workflow's either.

The narrower predicate that would render a pristine skeleton while still declining an edited
one — comparing the file against the template it came from — is deliberately not built here:
it needs `init.sh` to reason about which kit version a file was seeded from, which is a
mechanism with its own failure modes and its own ticket.

The templates have to land **before** `init.sh` runs, not with the other file copies in Step
4: `init.sh` resolves `docs/templates/*.tmpl` relative to the working directory, so without
them it prints `note: template … missing — skipped` and seeds nothing. For a repo whose
narrative docs are already in use that is merely noise (they would have been left untouched
anyway), but a **partially-adopted** repo missing one of the seeded docs would silently not
get it seeded — including the root `AGENTS.md` and `CLAUDE.md`, which on this upgrade path is
how an existing adopter first receives either at all.

Note this is also why running `/tmp/agentic-dev-kit/init.sh` in place of the copy is *not*
equivalent: every path it reads — the config, the templates — resolves against the working
directory, not against its own location, so it still needs the templates present here.

`init.sh` is the supported config upgrade path. **With `--no-clobber` it is safe to re-run
any number of times**; bare, it is not, and the difference is the table above rather than a
matter of degree. It only ever **adds** missing config keys, never guesses over an existing
value; it probes `paths.engines` from where engines actually are rather than defaulting; it
stamps `kit.version`; and it installs the pre-push hook as a shim (honoring
`core.hooksPath`).

For the seeded docs, what `--no-clobber` leaves standing is every file that already exists —
whether it is genuinely in use or still carries a marker. A file whose **first line opens an
HTML comment beginning with** the unrendered marker or the kit-own marker is the only kind
bare `init.sh` would have re-rendered, and it is exactly the kind this run declines and
reports instead.

Press Enter through every prompt to keep current values. Then re-read the diff of
`config/dev-model.yaml` and confirm nothing you rely on changed.

## Step 3 — Refresh engines, by state

Work through `kit_doctor`'s file list. You are already on the branch from Step 2 —
`init.sh` refreshed itself and migrated the config there, so those changes are captured
too. Confirm with `git branch --show-current` before the first copy.

**Every verdict below decides *whether* to take a file. None of them says what taking it
will change** — that is Step 1's changelog read, and it is the half this step used to
omit entirely. Have those entries to hand before the first copy: they are what makes a
red test afterwards an expected edit instead of an investigation (`#430`).

**Install every `missing-required` file first, before any other copy in this step.**
Those are the kit's own libraries — `<engine-dir>/lib/kitconfig.py` above all, which
every Python engine imports — and refreshing a component on top of an absent one
produces a broken install: `<engine-dir>/check_doc_budget.py` dies with
`ModuleNotFoundError`, and `<engine-dir>/pr_watch.py` warns and silently falls back to
built-in defaults, leaving the adopter's entire `review.*` config inert. `kit_doctor`
derives this set from the Python import graph, so it is answering "what do *this*
tree's installed components need", not a fixed list.

**Then re-run `kit_doctor` after installing anything.** The set is computed against the
components present *when the report ran*: a file is `missing-required` only if something
that depends on it is already installed. So installing a previously-`missing` engine or
hook can introduce requirements the first report had no reason to classify. Re-run
before you rely on the list again, and treat the report as converged only when a run
that installed nothing still shows no `missing-required`.

- **`missing-required`** → install it. This is the one absent-file case that is **not**
  an operator decision: an installed component depends on it, and the report names
  which. Do not carry it into the `missing` conversation below.
- **`unchanged`** → copy the new version straight in. It is provably untouched, so there
  is nothing to lose.
- **`removed`** → **not** an operator decision either, and not a sized-down adoption:
  this repo's own baseline records the file AS installed and it is gone now. Restore it,
  or — if the removal was deliberate — say so and let Step 4's `--record-install` write
  the new intent. Do not carry it into the `missing`/`declined` conversation below; the
  whole point of the state is that it is *not* one of those.
- **`declined`** → nothing to do, and nothing to ask. This repo recorded the file as
  absent when its baseline was written, so the omission is already the operator's
  answer. Do not re-litigate it: re-asking every upgrade is the noise the declared set
  exists to remove. Raise it only if the operator asks what was left out, or if a
  `missing-required` above now names it.
- **`new-upstream`** → **this is the decision `/upgrade` owns.** The baseline mentions the
  file in neither map; the ordinary cause is that the kit gained it after the baseline was
  recorded, so no declared set could have mentioned it and nobody has ever been asked.
  **Treat a `new-upstream` file you recognise as one this repo once installed as a
  finding, not as a new offer** — a damaged baseline produces this same state, and the
  report cannot tell the two apart (see `kit_doctor.py`'s `new-upstream` docstring). If
  that happens, restore from git history rather than accepting it as new.
  Otherwise ask now, once, per file — the same "decide, don't assume"
  conversation as `missing` below, but with a bounded list: only what is genuinely new
  since the last record. Whichever way it goes, Step 4's `--record-install` is what makes
  the answer durable; skip it and the same file is `new-upstream` again next upgrade.
- **`missing`** → decide, don't assume. **You only see this state when the repo has no
  declared install set** — a baseline predating it, or none at all — so the absences are
  undifferentiated and the three states above cannot be told apart. A sized-down adoption
  omits engines deliberately
  (one surveyed repo installs 2 of 6 on purpose). Ask the operator whether each missing
  piece is wanted before installing it. If a piece stays out, note it in the PR body so
  the next upgrade doesn't re-litigate it — and re-run `--record-install` in Step 4, which
  is what stops the next upgrade needing the PR body at all. Nothing installed here
  depends on these **by
  the graph `kit_doctor` derives**, which is what separates them from the bullet above.
  That graph covers **Python imports only** — it does not read shell `source`, so
  `<engine-dir>/lib/repo_root.sh` (which `<engine-dir>/dev_session.sh` and
  `<engine-dir>/reconcile_sessions.sh` both source) will appear here rather than
  above. It is a much better prior than the old blanket
  "decide, don't assume", not a proof: if a piece you are declining is a library a
  shell component plausibly reaches for, check before dropping it.
- **`STALE`** → replace it. The baseline proves it was never touched here, so the diff
  you would read is entirely kit-authored. This is the state that used to be reported as
  a likely local edit and cost a hand-diff each time.
- **`LOCALLY EDITED`** / **`STALE and LOCALLY EDITED`** → the `differs` procedure below,
  which is now reached only when there really is a local change to reconcile.
- **`differs`** (no baseline, or a file the baseline has no entry for) → `diff` the local
  file against the kit's, and read the diff:
  - Only kit-authored changes (the local copy is simply older) → replace it.
  - Local edits present → for each, find where that value now lives in
    `config/dev-model.yaml` and move it there, then take the kit's engine. If there is no
    config key for it, **stop**: that is the kit bug the invariant above describes. File
    it upstream and keep the local patch, clearly flagged, until it lands.
  - **Local edits that are genuinely ahead of the kit** — a fix made here first — are the
    one case to route *upstream* instead: open a PR against the kit rather than
    overwriting your better version.

  **If you keep a local patch, do not leave it in place through Step 4.** Step 4 records
  the baseline from the files as they sit, so a patch still applied here is recorded as
  *what the kit installed* — and every later upgrade then reports that file `STALE`,
  whose instruction is "replace it, nothing local is lost". The flag saying someone chose
  that patch is destroyed by the step meant to protect it. Set the patch aside now (take
  the kit's copy, keep the diff), let Step 4 record, then re-apply it. It will read
  `LOCALLY EDITED` from then on, which is the whole point.
- **`unknown-version`** → the manifest has no entry, so drift is unjudgeable. Treat as
  `differs` and diff by hand.

Never batch-replace the whole list because most of it was `unchanged`. The `differs`
entries are exactly where the risk is.

## Step 4 — Refresh the non-engine pieces

- **Shared workflows** (`docs/agentic-dev-kit/workflows/`) — same state logic as engines.
  These are prompts an agent reads verbatim; a stale one silently teaches old behavior.
- **Runtime adapters** (`.claude/commands/`, `.agents/skills/`) — follow Step 1's
  rendered comparison per path. Refresh `kit-stale`, leave `kit-current` alone,
  install `missing`, and report but preserve `adopter-owned`. Do not infer ownership
  from a slug or from the presence of a shared-workflow link: the byte comparison is
  what distinguishes generated glue from authored policy. An adapter migration that
  Step 1's selected changelog entry names as required to obtain changed gate semantics
  still needs an explicit reconciliation: move adopter policy into config or the shared
  workflow, then take the rendered binding. Stop for irreconcilable local behavior
  rather than retaining an adapter that bypasses the new gate. PR `#595`'s
  `post-merge-systemize` entry is the worked instance.
- **Templates** (`docs/templates/`) — refresh freely; the *rendered* docs are yours and
  are never touched.
- **`.claude/settings.json`** — if this repo has its own, **merge** the kit's hooks and
  permissions into it rather than replacing; it likely carries project-specific entries.

**Then record the baseline — this step is not optional, and its omission is what made
`differs` unjudgeable for every adopter until now:**

```bash
uv run "${REPO:?REPO is not set — re-run Step 0}"/<engine-dir>/kit_doctor.py --record-install --from-kit /tmp/agentic-dev-kit
```

This rewrites `kit-manifest.json` **here** to record what this repo now has installed —
**and, as `not_installed`, what it deliberately does not** — stamped with the kit commit
it came from. That second list is what carries Step 3's decisions forward: an absence in
it reports as `declined` rather than as an open question, so the next upgrade stops
asking. Skip this step and every decline you just made is re-asked next time, which is
the conversation the PR-body note was standing in for. Nothing else writes it: `/adopt` and `/upgrade`
copied kit files in and left this file at whatever it was on the day it first arrived, so
an adopter's baseline drifted further from its own tree with every upgrade. Measured on a
real adopter (2026-08-03): its manifest recorded `wrap-up.md` at the kit's 2026-07-15
version while the file beside it had been installed from a 2026-08-03 commit — nineteen
days of skew, against which three untouched files read as local edits.

**Order matters, and it is the reverse of what feels natural.** Run this *after the
copies and before re-applying any local patch you decided to keep*:

- A patch applied **after** recording reads as `LOCALLY EDITED` at every future upgrade —
  which is what you want for a patch you are carrying deliberately.
- A patch applied **before** recording is baked into the baseline and reads as `STALE`
  forever, silently losing the flag that says someone chose it.

Commit the rewritten `kit-manifest.json` with the rest of the upgrade.

## Step 5 — Verify

```bash
uv run "${REPO:?REPO is not set — re-run Step 0}"/<engine-dir>/kit_doctor.py --manifest /tmp/agentic-dev-kit/kit-manifest.json
tmp="$(mktemp -d)" && DEVKIT_STATE_ROOT="$tmp" uv run --with pytest --with pyyaml python "${REPO:?REPO is not set — re-run Step 0}"/<engine-dir>/run_installed_tests.py --root "$REPO" --engine-dir <engine-dir>
uv run "${REPO:?REPO is not set — re-run Step 0}"/<engine-dir>/check_doc_budget.py
```

**`DEVKIT_STATE_ROOT` is not optional here, and the `&&` is what makes it
fail closed.** `<engine-dir>/pr_watch.py` computes its persistence root once, at import
time — the only engine that reaches `state/` at all, and it resolves at
import rather than per call, so an override has to be in the environment
before the process starts. The resolution has three branches, not two:
`$DEVKIT_STATE_ROOT`,
then a `.devkit_state_root` marker walked up from the engine's own directory,
then `<repo>/state`. Outside a lane there is no marker, so absent the env var
the third branch is what you get — and running this suite then writes fixture
data straight into this repo's live `state/pr-watch/`, the merge gate's own
evidence store, while the run otherwise looks clean. `#428` measured it: an unpatched run overwrote
`state/pr-watch/1.json` and `4242.json` with a fabricated review receipt and
a reset `seen` set. A conftest fixture closes this for anyone who has it (see
`scripts/tests/conftest.py`'s `_hermetic_state_root`), but this command is
the independent outer layer: it protects a sized-down adopter whose declared
install set includes a runnable test module without every conftest or sibling test.
Test paths are kit-owned and upgradeable now, but they remain individually declinable,
so a partial test surface is a supported case rather than evidence of a broken
upgrade. The runner reads the adopter's `kit-manifest.json`, invokes only declared
top-level `test_*.py` modules under the configured engine's test roots, and says when
there are none. A present but undeclared test is not part of the installed kit suite;
a declared module whose support imports were declined is an inconsistent installation
and fails collection rather than being silently skipped. The runner avoids passing a
declined directory to pytest and stopping before an installed test can run. That is the
current form of the case
`#40`/`#132` first exposed.

Write it as the two-step `tmp="$(mktemp -d)" && …`, not as an inline
`DEVKIT_STATE_ROOT=$(mktemp -d) …`. The inline form fails **open**: a failed
`mktemp -d` prints nothing to stdout, so the var is set to the empty string,
and `_resolve_state_root` treats an empty value as *no override at all* and
falls back to the repo default — landing the whole suite in live `state/`,
which is the one outcome this line exists to prevent. The `&&` makes the
assignment's exit status gate the run, so a failed `mktemp` skips the tests
instead of silently redirecting them at the thing they would damage.

`kit_doctor` should now report zero mismatches of every kind — `differs`, `STALE`,
`STALE and LOCALLY EDITED` — and zero `unknown-version`. `LOCALLY EDITED` should be zero
**except for the local patches you deliberately kept in Step 3 and can name**; see the
paragraph below, which is the one expected exception rather than a caveat on the rule.
Because Step 4
has just written a declared install set, the absences should now read
`✓ intact for this adoption — N file(s) declined` rather than a bare `missing` count, with
**zero `removed` and zero `new-upstream`**: the first would mean something was deleted
after the record, the second that a file you were offered in Step 3 was neither installed
nor recorded as declined. Anything else means Step 3 left something.

A **`missing`** count surviving this step is itself a finding: Step 4 writes the declared
set, so the state it eliminates should not be reachable here. The report's own `baseline:`
note names the causes; these are the ones worth knowing, and the second is the one you
will actually hit:

- `--record-install` did not run, or ran against a different root.
- The baseline predates the declared install set, or its `files` / `not_installed` value
  is malformed — `kit_doctor` declines to read a scope out of either, rather than guess.
- **Step 4 reported unverified paths.** One kit-owned file that is present but does not
  byte-match the source kit suppresses the **entire** `not_installed` key — the record is
  partial, so it declares no scope at all, for every file rather than just that one — and
  `--record-install` exits 1 saying so. A local patch you kept but did not set aside per
  Step 4's ordering rule is the usual way in. Reconcile the paths it named, then re-run.

**The `baseline:` note cannot tell the second cause from the third**, so do not read it as
deciding between them: an absent declared set is the only evidence either leaves, and a
baseline written moments ago by a current kit looks identical to an old one. The note says
so. What distinguishes them is Step 4's own output — `--record-install` exits 1 and lists
the unverified paths — so check that, not the note.

That exception, stated once: a local patch you chose to keep in Step 3 reports
`LOCALLY EDITED`, which is the baseline working as intended. Name it in the PR body so
the next upgrade does not re-litigate it. A `LOCALLY EDITED` file you cannot name is not
this case — it is Step 3 leaving something.

It should also now print a `baseline:` line naming the kit commit you installed from —
and **the sha it names has to be checked, not just the line's presence.** On a repeat
upgrade the previous cycle's baseline is still on disk, so a skipped Step 4 prints a
perfectly well-formed line naming the commit you upgraded from *last* time:

```sh
git -C /tmp/agentic-dev-kit rev-parse HEAD   # the baseline: line shows its first 12 chars
```

`none recorded` means Step 4's `--record-install` never ran. A line reading `compared
against ITSELF` means you invoked `kit_doctor` bare — that run has no upstream in it and
cannot report staleness at all; re-run it with `--manifest` as shown above.

> **Known gotcha:** the `state_paths` tests fail when run from inside a worktree carrying
> a `.devkit_state_root` marker — the fixture neutralizes the environment but not marker
> discovery. Run the gate from the main checkout, and see kit issue #10.

## Step 6 — Record the friction, then hand off

Append anything this upgrade surfaced to the friction log (`paths.friction_log`) — an
engine you had to edit, a config key that didn't exist, a `missing` piece the report
couldn't classify. Tag `[kit]` on anything that is a kit-side fix and open an issue
upstream. That is Principle #2 applied to the kit itself, and it is how the four shapes
this skill handles were discovered in the first place.

Open a **draft PR** summarizing: schema version before → after, which engines were
refreshed / diffed / deliberately skipped, and any local-edit-vs-config resolution you
made. Leave the merge to the operator — an upgrade touches the machinery every other
workflow runs on.
