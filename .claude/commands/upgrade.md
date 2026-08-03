---
description: Upgrade an already-adopted agentic-dev-kit installation to the current kit — migrate the config schema, refresh kit-owned engines, and diff anything that drifted. The counterpart to /adopt (first install) and to re-running ./init.sh (config only). Use when pulling a kit update into a repo that already has the kit.
argument-hint: "[--dry-run]"
---

Upgrade this repo's agentic-dev-kit installation. Non-destructive: runs on a branch, and
never replaces a file without knowing it is safe to replace.

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

Everything below copies **from** that checkout **into** this repo.

## Step 1 — Diff the installation (read-only)

```bash
uv run <engine-dir>/kit_doctor.py --manifest /tmp/agentic-dev-kit/kit-manifest.json
```

Read `<engine-dir>` from `paths.engines`. If `kit_doctor.py` isn't installed yet, run the
kit's copy against this repo: `uv run /tmp/agentic-dev-kit/scripts/kit_doctor.py --root .
--manifest /tmp/agentic-dev-kit/kit-manifest.json`.

The report gives you, per kit-owned file: `unchanged` / `differs` / `missing` /
`missing-required` / `unknown-version`, plus four installation-level checks.
**Read all four** — each is a silent failure mode:

- **config schema version** — unversioned or behind means migrations are pending.
- **`paths.engines` resolves to a directory that actually holds engines.** A `✗` here is
  the live breakage where every workflow's `<engine-dir>/…` reference points at nothing.
  Nothing else validates this value, so nothing else would have told you.
- **pre-push hook installed** — a shipped-but-uninstalled hook binds nothing.
- **narrative docs rendered** — a doc whose **first line** still carries
  `devkit-template: unrendered` means the adoption never completed its seeding step. A
  doc that merely quotes the marker further down is in use and is reported as such.

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

## Step 2 — Branch, refresh the migrator, then migrate

**Branch first.** Everything from here mutates the repo — config, hooks, rendered
docs — so the "runs on a branch" guarantee has to be established *before* the first
mutation, not before the file copies in Step 3:

```bash
git checkout -b chore/kit-upgrade
```

**Then refresh `init.sh` itself before running it.** This is the step that is easy to get
backwards: the repo's existing `init.sh` is the *old* one, and it does not contain the new
schema migrations — so running it would report success while silently applying nothing new.
Take the fetched kit's copy first:

```bash
cp /tmp/agentic-dev-kit/init.sh ./init.sh
chmod +x init.sh                                  # the kit ships it 100755; a copy can lose the bit
mkdir -p docs/templates && cp /tmp/agentic-dev-kit/docs/templates/*.tmpl docs/templates/
./init.sh
```

The templates have to land **before** `init.sh` runs, not with the other file copies in Step
4: `init.sh` resolves `docs/templates/*.tmpl` relative to the working directory, so without
them it prints `note: template … missing — skipped` and seeds nothing. For a repo whose
narrative docs are already in use that is merely noise (they would have been left untouched
anyway), but a **partially-adopted** repo missing one of the seeded docs would silently not
get it seeded — including the root `AGENTS.md`, which on this upgrade path is how an existing
adopter first receives one at all.

Note this is also why running `/tmp/agentic-dev-kit/init.sh` in place of the copy is *not*
equivalent: every path it reads — the config, the templates — resolves against the working
directory, not against its own location, so it still needs the templates present here.

`init.sh` is the supported config upgrade path, and it is safe to re-run any number of times.
It only ever **adds** missing keys, never guesses over an existing value; it probes
`paths.engines` from where engines actually are rather than defaulting; it stamps
`kit.version`; it installs the pre-push hook as a shim (honoring `core.hooksPath`); and
it leaves a narrative doc that is genuinely in use byte-identical, re-rendering only one
whose **first line** still carries the unrendered marker.

Press Enter through every prompt to keep current values. Then re-read the diff of
`config/dev-model.yaml` and confirm nothing you rely on changed.

## Step 3 — Refresh engines, by state

Work through `kit_doctor`'s file list. You are already on the branch from Step 2 —
`init.sh` refreshed itself and migrated the config there, so those changes are captured
too. Confirm with `git branch --show-current` before the first copy.

**Install every `missing-required` file first, before any other copy in this step.**
Those are the kit's own libraries — `lib/kitconfig.py` above all, which every Python
engine imports — and refreshing a component on top of an absent one produces a broken
install: `check_doc_budget.py` dies with `ModuleNotFoundError`, and `pr_watch.py` warns
and silently falls back to built-in defaults, leaving the adopter's entire `review.*`
config inert. `kit_doctor` derives this set from the Python import graph, so it is
answering "what do *this* tree's installed components need", not a fixed list.

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
- **`missing`** → decide, don't assume. A sized-down adoption omits engines deliberately
  (one surveyed repo installs 2 of 6 on purpose). Ask the operator whether each missing
  piece is wanted before installing it. If a piece stays out, note it in the PR body so
  the next upgrade doesn't re-litigate it. Nothing installed here depends on these **by
  the graph `kit_doctor` derives**, which is what separates them from the bullet above.
  That graph covers **Python imports only** — it does not read shell `source`, so
  `lib/repo_root.sh` (which `dev_session.sh` and `reconcile_sessions.sh` both source)
  will appear here rather than above. It is a much better prior than the old blanket
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
- **Runtime adapters** (`.claude/commands/`, `.agents/skills/`) — install any the kit has
  that this repo lacks; keep the adopter's version where one already exists.
- **Templates** (`docs/templates/`) — refresh freely; the *rendered* docs are yours and
  are never touched.
- **`.claude/settings.json`** — if this repo has its own, **merge** the kit's hooks and
  permissions into it rather than replacing; it likely carries project-specific entries.

**Then record the baseline — this step is not optional, and its omission is what made
`differs` unjudgeable for every adopter until now:**

```bash
uv run <engine-dir>/kit_doctor.py --record-install --from-kit /tmp/agentic-dev-kit
```

This rewrites `kit-manifest.json` **here** to record what this repo now has installed,
stamped with the kit commit it came from. Nothing else writes it: `/adopt` and `/upgrade`
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
uv run <engine-dir>/kit_doctor.py --manifest /tmp/agentic-dev-kit/kit-manifest.json
uv run --with pytest --with pyyaml python -m pytest <engine-dir>/lib/state_paths/tests <engine-dir>/tests -q
uv run <engine-dir>/check_doc_budget.py
```

`kit_doctor` should now report zero mismatches of every kind — `differs`, `STALE`,
`LOCALLY EDITED`, `STALE and LOCALLY EDITED` — and zero `unknown-version`, with `missing`
containing only deliberately-omitted pieces. Anything else means Step 3 left something.

The one expected exception is a local patch you chose to keep in Step 3: it reports
`LOCALLY EDITED`, which is the baseline working as intended. Name it in the PR body so
the next upgrade does not re-litigate it.

It should also now print a `baseline:` line naming the kit commit you installed from. If
it still says `none recorded`, Step 4's `--record-install` did not run.

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
