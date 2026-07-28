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
`unknown-version`, plus four installation-level checks. **Read all four** — each is a
silent failure mode:

- **config schema version** — unversioned or behind means migrations are pending.
- **`paths.engines` resolves to a directory that actually holds engines.** A `✗` here is
  the live breakage where every workflow's `<engine-dir>/…` reference points at nothing.
  Nothing else validates this value, so nothing else would have told you.
- **pre-push hook installed** — a shipped-but-uninstalled hook binds nothing.
- **narrative docs rendered** — a doc whose **first line** still carries
  `devkit-template: unrendered` means the adoption never completed its seeding step. A
  doc that merely quotes the marker further down is in use and is reported as such.

`differs` deliberately does **not** claim a cause: a hash mismatch cannot distinguish
"older kit version" from "hand-edited". The report narrows it by schema version; you
confirm with an actual diff in Step 3.

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

- **`unchanged`** → copy the new version straight in. It is provably untouched, so there
  is nothing to lose.
- **`missing`** → decide, don't assume. A sized-down adoption omits engines deliberately
  (one surveyed repo installs 2 of 6 on purpose). Ask the operator whether each missing
  piece is wanted before installing it. If a piece stays out, note it in the PR body so
  the next upgrade doesn't re-litigate it.
- **`differs`** → `diff` the local file against the kit's, and read the diff:
  - Only kit-authored changes (the local copy is simply older) → replace it.
  - Local edits present → for each, find where that value now lives in
    `config/dev-model.yaml` and move it there, then take the kit's engine. If there is no
    config key for it, **stop**: that is the kit bug the invariant above describes. File
    it upstream and keep the local patch, clearly flagged, until it lands.
  - **Local edits that are genuinely ahead of the kit** — a fix made here first — are the
    one case to route *upstream* instead: open a PR against the kit rather than
    overwriting your better version.
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

## Step 5 — Verify

```bash
uv run <engine-dir>/kit_doctor.py --manifest /tmp/agentic-dev-kit/kit-manifest.json
python -m pytest <engine-dir>/lib/state_paths/tests <engine-dir>/tests -q
uv run <engine-dir>/check_doc_budget.py
```

`kit_doctor` should now report zero `differs` and zero `unknown-version`, with `missing`
containing only deliberately-omitted pieces. Anything else means Step 3 left something.

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
