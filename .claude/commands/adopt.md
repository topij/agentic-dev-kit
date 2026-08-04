---
description: Selectively adopt agentic-dev-kit into an existing repo — inspect what's already present, propose an install plan the operator confirms, then install only the missing pieces without clobbering existing files. Use when integrating the kit into a mature repository rather than a fresh one.
---

Selectively adopt agentic-dev-kit into an **existing** repo — install only the pieces
the repo lacks, point the config at conventions it already has, and never clobber a
file. The counterpart to `init.sh` (which assumes a fresh/near-empty repo). Runs
non-destructively on a branch; the operator confirms the plan before anything is written.

> **Why a skill, not `cp -r`.** A blind copy-in clobbers existing agent adapters, config,
> plan doc, and CI. Adopting into a mature repo is a *judgment* pass — which pieces are
> already present, where the scripts should live, what the config should point at — so
> it's a guided skill, not a script.

## Step 0 — Fetch the kit

If the kit isn't already checked out locally, shallow-clone it to a temp dir (use your
own fork's URL if you maintain one):

```bash
git clone --depth 1 https://github.com/topij/agentic-dev-kit /tmp/agentic-dev-kit
```

Everything below copies FROM that checkout INTO the current repo (the adopter). Run all
of it from the target repo's root.

## Step 1 — Inspect the target repo (read-only)

Run these probes and record the answers — they drive the plan:

- **Living plan?** `ls ROADMAP.md PLAN.md docs/plan.md docs/handoff.md handoff.md 2>/dev/null`. If one exists, the repo already practices Principle #1 — you'll point the kit at it, not add a second plan.
- **Skill collisions?** Inspect `.claude/commands/` and `.agents/skills/`. Which of the kit's workflows already exist for either runtime? Keep the adopter's implementation and install only the missing adapters.
- **Root entry points?** Classify each of `AGENTS.md` and `CLAUDE.md` into **three** states, not two — presence alone is not enough, and getting this wrong destroys files:

  ```sh
  for f in AGENTS.md CLAUDE.md; do
    if [ ! -e "$f" ]; then echo "$f: ABSENT — will be seeded"
    elif head -n 1 "$f" | LC_ALL=C sed -n 's/^<!--[[:space:]]*//p' \
         | grep -qE '^(devkit-template: unrendered|devkit-source: kit-own)([[:space:]]|$)'
    then echo "$f: MARKED — init.sh WILL RENDER OVER IT"
    else echo "$f: IN USE — left byte-identical"
    fi
  done
  # record the hashes Step 4 verifies against (GNU spelling: sha256sum)
  shasum -a 256 AGENTS.md CLAUDE.md 2>/dev/null > step1-hashes.txt
  ```

  `step1-hashes.txt` is scratch — write it outside the worktree, or delete it before the
  PR; it must not land in the adoption commit.

  **`MARKED` is the dangerous state and it is not hypothetical.** A file whose first
  line carries a kit marker is *seedable* — `init.sh` renders over it and reports only
  `seeded`, with **no backup**. Verified: an `AGENTS.md` opening with
  `<!-- devkit-source: kit-own -->` and carrying paragraphs of adopter doctrine below it
  was replaced wholesale, and the doctrine was unrecoverable. That is correct for
  `init.sh` on a fresh repo or an upgrade — the marker is how the kit re-renders its own
  skeletons — but it directly contradicts this skill's "never overwrite an existing file"
  contract. The adopter who hits it is the one who took the pre-`#288` `cp -r` quickstart
  and then edited what landed, which is a shipped path, not an edge case.

  Record the hashes above whatever the state: Step 4 verifies against them, because
  `git diff` proves nothing for a file that is untracked or gitignored.
- **Config dir?** `ls -d config 2>/dev/null` — where `config/dev-model.yaml` goes (repo root if there's no `config/`).
- **`scripts/` layout?** `ls scripts 2>/dev/null`. **Default to vendoring the kit's engines under `scripts/devkit/`.** It is required when `scripts/` is organized into subdirs or has colliding filenames, and it is the right call anyway whenever the repo lints or formats repo-wide (next bullet) — a directory is the only unit you can exclude without maintaining a filename list. Flat `scripts/` is only appropriate for a repo with no repo-wide lint and no collisions.
- **Tracker?** `gh issue list -L1 2>/dev/null` succeeds → GitHub Issues; else look for a Linear/Jira setup. Sets `tracker.backend`.
- **Review bot?** Do NOT infer from a config file — a repo can have CodeRabbit/Bugbot enabled org-wide with no in-repo config. Check a recent PR or the org settings. Sets `review.bots`.
- **CI/lint scope?** Read `.pre-commit-config.yaml` + `.github/workflows/`. Does lint run repo-wide or scoped to a package dir? If **anything** lints or formats repo-wide, read [`adopting-into-a-linted-repo.md`](../../docs/agentic-dev-kit/adopting-into-a-linted-repo.md) before writing a single file, and plan the engines directory around it.

  Two failures, and the second is the dangerous one:
  - **Red CI** — a repo-wide ruff trips on the kit's `state_paths` tests (bare `assert`, `S101`) and on engine findings the kit's own lint doesn't select. Visible, annoying, harmless.
  - **A formatter silently rewriting kit-owned engines** — `ruff --fix`, `ruff-format`, black, even a trailing-whitespace hook. Measured on a real adoption (issue #58): the first `pre-commit run` after install rewrote **both** installed Python engines. `kit_doctor` *does* catch this and exits 1 — it is not defeated by it — but the damage is that the finding never clears: the formatter rewrites the file again after every refresh, so every engine sits permanently at `differs` and `/upgrade` Step 3 can no longer use that signal to tell "simply older" from "locally edited".

  Consequence for the Step 3 placement below: **give the engines their own directory** (`scripts/devkit/`) even when no filenames collide, because a directory is the only exclusion unit that doesn't drift as the kit adds files.

## Step 2 — Propose the adoption plan, then wait

Present a table the operator confirms **before any write**:

| Kit piece | Repo today | Action |
|---|---|---|
| Living plan (#1) | e.g. has `ROADMAP.md` | **config-point** `paths.handoff` → it; keep it (or offer to rename → `handoff.md`) |
| `wrap-up` skill | has its own | **skip** |
| Codex adapters | none | **install** under `.agents/skills/` |
| friction-log (#2) | none | **install** |
| parallel + `state_paths` (#3) | none | **install** under `scripts/devkit/` (see Step 1 on when flat `scripts/` is acceptable) |
| `pr-watch` (#5), safety rule (#6) | none | **install** |
| Root entry points | e.g. `AGENTS.md` ABSENT, `CLAUDE.md` IN USE | **seed the absent one** from `docs/templates/` via `init.sh`; an IN USE one is left byte-identical |
| — a `MARKED` entry point | e.g. `AGENTS.md` MARKED | **destructive — call it out by name and get an explicit yes.** Default to *preserving* it (Step 3b); re-rendering discards everything below line 1 |
| pre-push hook | not installed | **install** the shim (`init.sh` does this; nothing else does) |
| tracker | e.g. GitHub Issues | `tracker.backend: github-issues` |
| review bot | e.g. CodeRabbit (org) | `review.bots: [coderabbit]` |

State the scripts placement, whether the repo's CI/lint needs a kit-dir exclude, and
that everything lands on a branch. **Do not proceed until the operator confirms.**

## Step 3 — Execute (on a branch, non-destructively)

```bash
git checkout -b chore/adopt-agentic-dev-kit
```

For each piece, **copy only if the target doesn't already exist**:

- **Shared workflows** → `docs/agentic-dev-kit/workflows/`.
- **Runtime adapters** → `.claude/commands/` and `.agents/skills/` (skip any target that collides with an existing workflow).
- **Engine scripts** → `scripts/devkit/` (flat `scripts/` only under the Step-1 conditions). Set `paths.engines` to that directory; do not rewrite prompt files. The engines find the repo root by walking up for `.git`, which is unbounded, so any depth works in a real checkout. In a tree with **no `.git` at all** the fallback is depth arithmetic calibrated for `scripts/` and resolves a vendored layout to the wrong directory — a known, deliberate limitation (issue #60); it fails loudly rather than guessing.
- **Safety doctrine** → `docs/agentic-dev-kit/safety-critical-changes.md`; install the thin `.claude/rules/safety-critical-changes.md` adapter when absent and merge `docs/AGENTS-sections.md` into an existing `AGENTS.md` when applicable.
- **Lint-containment doctrine** → `docs/agentic-dev-kit/adopting-into-a-linted-repo.md`. Install it whenever Step 1 found repo-wide lint or format, and apply its exclusions **in the same commit as the engines** — an engine that gets autoformatted before the exclusion lands is already drifted. `kit_doctor` tracks this file, so skipping it shows up as a permanent `missing`.
- **`config/dev-model.yaml`** — stamp the Step-1 values: `paths.handoff` → the existing plan (and `paths.handoff_history` / the `doc_budgets` entry to match), `paths.engines`, `runtime`, `tracker`, `review`, and `models`. **`review:` must exist as a key before Step 3b runs**, even if you only know `review.bots` — `init.sh` fills a *partial* `review:` section in completely, but cannot create one from nothing and emits seven `could not add review.*` warnings instead (measured; the `runtime:` section has no such limitation, which is why this is easy to miss).
- **`docs/templates/`** — all six `.md.tmpl` files. They are **manifest-tracked**, so omitting them is not merely a missed convenience: `kit_doctor` then reports six extra `missing` entries tagged `[template]` (measured), and Step 4 tells you to expect `missing` only for pieces Step 2 deliberately dropped. They are also the input Step 3b renders from.
- **`init.sh`** — copy it to the adopter root. It is manifest-*untracked*, so it does not affect the baseline; Step 3b runs it.
- **`friction-log.md`** — seeded by Step 3b from the template, not hand-copied.
- Copy `PRINCIPLES.md`, `docs/parallel-dev.md`, and the shared workflow/safety docs under `docs/agentic-dev-kit/` for reference.

**Never overwrite an existing file.** If something you didn't anticipate collides, stop
and ask the operator.

### Step 3b — run `init.sh` non-interactively

**First, preserve any `MARKED` entry point Step 1 found.** `init.sh` will render over it
otherwise, and nothing else in this flow will stop that:

```bash
# only for a file Step 1 classified MARKED
cp -p AGENTS.md AGENTS.md.pre-adopt      # and/or CLAUDE.md
```

Unless the operator explicitly chose to re-render it, restore it after Step 3b and hand
them the `.pre-adopt` copy to reconcile — the rendered template and their edits both have
a claim, and merging them is a judgment call, not something to do silently. Never delete
the `.pre-adopt` copy yourself.

Then, with the config stamped and `docs/templates/` in place:

```bash
./init.sh < /dev/null
```

**Redirecting stdin is the whole mechanism, not a formality.** With no terminal
attached, `init.sh` announces `keeping all current config/dev-model.yaml values` and
every prompt takes the value you just stamped — so it never interrogates the operator
and never overwrites a Step-1 decision. This is what seeds `AGENTS.md`, and it replaces
the four things this skill used to tell you to do by hand:

- **Seeds `AGENTS.md` and `CLAUDE.md`** from `docs/templates/`, each when the target is
  missing **or carries a kit marker on line 1** — the second half is the destructive one
  Step 1 classifies as `MARKED`. An entry point carrying *neither* marker is left
  **byte-identical** and reported as `already in use`. Do not
  hand-render these instead: `_seedable` is the guard whose three separate
  file-destroying defects `#288` closed by mutation testing (a *directory* named
  `AGENTS.md`; a marker matched as an unanchored substring; a locale-dependent
  `[[:space:]]`), and `_render` substitutes through awk-via-`ENVIRON` specifically
  because a tracker URL containing `/`, `&` or `\` is mangled by `sed` and by awk `-v`.
  A hand-rolled copy-if-absent reintroduces that entire class.
- **Installs the pre-push hook** as a shim honoring `core.hooksPath`, pointing at the
  engines directory you chose. Nothing else in this skill did — so before this step,
  every `/adopt` adoption left the kit's own mechanism-over-memory exemplar inert.
- **Appends the `.gitignore` entries**, including **`config/*.local.yaml`**, which is
  load-bearing: `kitconfig.load_config()` merges a gitignored
  `config/dev-model.local.yaml` over the tracked config, and `docs/getting-started.md`
  tells the operator to put their DM id there. Without it an identity lands in a tracked
  path while every doc says it is ignored.
- **Seeds the narrative docs** — and correctly declines the ones already in use, so an
  adopter whose `paths.handoff` points at an existing `ROADMAP.md` keeps it untouched.

**It rewrites `config/dev-model.yaml` in place.** Not lossily — comments survive — but
it adds the `kit:` and `runtime:` sections and re-quotes scalars carrying YAML
indicators (a tracker URL gains surrounding quotes). Commit the config before running so
the rewrite is reviewable as its own diff.

**Read its output.** Two lines matter and neither is an error:

- `<path> already in use — left untouched` — the guard working. Confirm the path named
  is one you expected to keep.
- `note: CLAUDE.md does not import AGENTS.md` — fires when the adopter had their own
  `CLAUDE.md`, which the guard correctly refused to touch. The consequence is that the
  two runtimes now read *different* contracts, which is the exact divergence the pair
  exists to prevent. **Never edit their file to fix it**; raise it with the operator and
  let them add the `@AGENTS.md` line.

### Step 3c — record the drift baseline

**Last, once every copy above and Step 3b are done:**

```bash
uv run <engines-dir>/kit_doctor.py --record-install --from-kit <kit checkout>
```

Order matters in one direction only: `docs/templates/` is manifest-tracked and must be
copied *before* this runs. Step 3b's own writes are safely outside the baseline —
`AGENTS.md`, `CLAUDE.md`, `init.sh` and `config/dev-model.yaml` are all
manifest-untracked, the rendered entry points because they are adopter-owned and meant
to be edited.

This writes `kit-manifest.json` here, recording which kit-owned files this adoption
actually installed and the kit commit they came from. It is what lets a later
`/upgrade` tell a **stale** file from a **hand-edited** one instead of guessing — the
guess was wrong for the commonest case and told adopters to hunt for edits they never
made (kit `#51`). Run it **after** the copies, so it records what landed; a sized-down
adoption is recorded as exactly the subset it installed.

**Pass `--from-kit`, and read what it prints.** With it, only files matching that
checkout are recorded — which is what keeps the "copy only if the target doesn't already
exist" rule above from backfiring. A file this adoption *retained* rather than copied
(an adopter's own file already sitting at a kit-owned path) is not the kit's, and
recording it would make the next `/upgrade` report it `STALE` — wording that says
"replace them, nothing local is lost" about a file that is entirely theirs. Any such
path is named on stderr and left out of the baseline; reconcile each with the operator
before re-running, and never silence it by dropping the flag.

## Step 4 — Verify

- **Entry points** — verify **every** file Step 3b could have touched, against the Step-1
  hashes. Do not use `git diff` for this: it reports nothing for an untracked or
  gitignored file, so a destroyed one looks clean.

  ```sh
  # every file that was ABSENT and got seeded: fully rendered?
  for f in AGENTS.md CLAUDE.md; do
    [ -f "$f" ] && echo "$f: $(grep -c '{{[A-Z_]*}}' "$f") unsubstituted tokens (want 0)"
  done
  # every file that was IN USE: byte-identical to what Step 1 recorded?
  #   an ABSENT file has no Step-1 line, so it is simply not checked here
  shasum -a 256 -c step1-hashes.txt
  ```

  A non-zero token count is the failure worth catching: it means the file was *copied*
  rather than rendered, which is what happens if someone substitutes `cp` for Step 3b. A
  hash mismatch on an `IN USE` file means the guard did not hold — stop and restore from
  the `.pre-adopt` copy or from git before doing anything else.
- **Hook** — resolve the directory the way `init.sh` does. `core.hooksPath` wins over
  `.git/hooks` when set (pre-commit and several monorepo setups set it), so checking
  `.git/hooks/pre-push` can inspect a file git will never run — or miss the one it will:

  ```sh
  hookdir="$(git config --get core.hooksPath || git rev-parse --git-path hooks)"
  grep -l devkit-hook-shim "$hookdir/pre-push"   # it is the kit's shim, not a stray hook
  grep -o "$(grep -E '^[[:space:]]+engines:' config/dev-model.yaml | awk '{print $2}')" \
    "$hookdir/pre-push"                          # and it targets the engines dir you chose
  ```

  `init.sh` refuses to replace a **non-shim** hook already at that path — it prints
  `existing <path> left untouched (not a kit shim) — chain it to <src> by hand` and moves
  on. That is the right call, and it means a repo with its own `pre-push` finishes this
  step with the kit's hook **not installed**. Read for that line and chain it, rather than
  assuming the hook is live because Step 3b exited 0.
- Portability tests: run the kit's suites explicitly. `/adopt` does not install the kit's
  `Makefile`, and a mature repo's own `make test` will run *its* suite, not these:

  ```sh
  uv run --with pytest --with pyyaml python -m pytest \
    scripts/devkit/lib/state_paths/tests/ scripts/devkit/tests/ -q
  ```

  (Adjust the prefix when engines live directly under `scripts/`.)
- `check_doc_budget`: run it — it should read the configured plan via `config/dev-model.yaml`.
- `kit_doctor`: run it **against the kit checkout's manifest**, not bare:

  ```sh
  uv run <engines-dir>/kit_doctor.py --manifest <kit checkout>/kit-manifest.json
  ```

  Bare, it compares this repo against the baseline Step 3 just wrote from these same
  files, so every recorded file matches *by construction* and the check establishes
  nothing — it would pass over a file that was copied wrong. The kit's manifest is an
  independent reference, and it is also the only one carrying `required_by`, which is
  what makes the `missing-required` axis work at all.

  Expect zero mismatches and `missing` containing only the pieces Step 2 deliberately
  left out.

  **Then check the `baseline:` line by comparing the sha it prints**, not merely that it
  is present. It reports what the baseline *claims*, so a leftover baseline from an
  earlier attempt prints a real-looking line naming the wrong commit:

  ```sh
  git -C <kit checkout> rev-parse HEAD    # the baseline: line shows its first 12 chars
  ```

  `baseline: none recorded` means Step 3's `--record-install` did not run at all.
- Confirm the repo's CI/lint scope **skips** the kit files (or add a kit-dir exclude if lint is repo-wide).

## Step 5 — Record the friction (the flywheel's first turn)

Seed `friction-log.md`'s first dated entry with every adoption friction you hit — a
skill collision, a namespacing rewrite, a tracker mismatch, a CI-scope surprise, a
review-bot detection miss. Tag `[kit]` on anything that's a kit-side fix and open an
issue upstream. This first entry *is* Principle #2 in action.

## Step 6 — Summarize + hand off

Report what was **installed / skipped / config-pointed**, open a **draft PR**, and
suggest the operator's first `/session-start` (Claude) or `$session-start` (Codex).
Leave the merge to the operator — an
adoption touches a lot of the repo and deserves a human review pass.
