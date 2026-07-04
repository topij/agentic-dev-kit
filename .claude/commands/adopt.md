Selectively adopt agentic-dev-kit into an **existing** repo — install only the pieces
the repo lacks, point the config at conventions it already has, and never clobber a
file. The counterpart to `init.sh` (which assumes a fresh/near-empty repo). Runs
non-destructively on a branch; the operator confirms the plan before anything is written.

> **Why a skill, not `cp -r`.** A blind copy-in clobbers an existing `.claude/`, config,
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
- **Skill collisions?** `ls .claude/commands/ 2>/dev/null` — which of the kit's skills (`session-start`, `wrap-up`, `parallel`, `pr-watch`, `triage-friction-log`, `post-merge-systemize`) already exist? Keep theirs; install only the rest.
- **Config dir?** `ls -d config 2>/dev/null` — where `config/dev-model.yaml` goes (repo root if there's no `config/`).
- **`scripts/` layout?** `ls scripts 2>/dev/null` — if it's organized into subdirs, or has files that collide with the kit's script names, vendor the kit's under `scripts/devkit/`; otherwise `scripts/` is fine.
- **Tracker?** `gh issue list -L1 2>/dev/null` succeeds → GitHub Issues; else look for a Linear/Jira setup. Sets `tracker.backend`.
- **Review bot?** Do NOT infer from a config file — a repo can have CodeRabbit/Bugbot enabled org-wide with no in-repo config. Check a recent PR or the org settings. Sets `review.bots`.
- **CI/lint scope?** Read `.pre-commit-config.yaml` + `.github/workflows/`. Does lint run repo-wide or scoped to a package dir? A **repo-wide** ruff will trip on the kit's `state_paths` tests (bare `assert`, `S101`) unless the kit's dir is excluded — flag it now.

## Step 2 — Propose the adoption plan, then wait

Present a table the operator confirms **before any write**:

| Kit piece | Repo today | Action |
|---|---|---|
| Living plan (#1) | e.g. has `ROADMAP.md` | **config-point** `paths.handoff` → it; keep it (or offer to rename → `handoff.md`) |
| `wrap-up` skill | has its own | **skip** |
| friction-log (#2) | none | **install** |
| parallel + `state_paths` (#3) | none | **install** (under `scripts/devkit/` if `scripts/` is organized) |
| `pr-watch` (#5), safety rule (#6) | none | **install** |
| tracker | e.g. GitHub Issues | `tracker.backend: github-issues` |
| review bot | e.g. CodeRabbit (org) | `review.bots: [coderabbit]` |

State the scripts placement, whether the repo's CI/lint needs a kit-dir exclude, and
that everything lands on a branch. **Do not proceed until the operator confirms.**

## Step 3 — Execute (on a branch, non-destructively)

```bash
git checkout -b chore/adopt-agentic-dev-kit
```

For each piece, **copy only if the target doesn't already exist**:

- **Skills** → `.claude/commands/` (skip any that collide with an existing one).
- **Engine scripts** → `scripts/devkit/` (or `scripts/` if clean). If you namespaced them, rewrite the `scripts/…` references in the copied skills to match (`sed -i '' 's#scripts/#scripts/devkit/#g' .claude/commands/<skill>.md`). The scripts find the repo root by walking up for `.git`, so they work at any depth.
- **`.claude/rules/safety-critical-changes.md`** (skip if present).
- **`config/dev-model.yaml`** — stamp the Step-1 values: `paths.handoff` → the existing plan (and `paths.handoff_history` / the `doc_budgets` entry to match), `tracker`, `review`, `models`.
- **`friction-log.md`** (seed only if absent).
- Append `state/` and `.devkit_state_root` to `.gitignore` if missing.
- Copy `PRINCIPLES.md` + `docs/parallel-dev.md` under `docs/agentic-dev-kit/` for reference.

**Never overwrite an existing file.** If something you didn't anticipate collides, stop
and ask the operator.

## Step 4 — Verify

- `state_paths` tests: `cd scripts/devkit/lib && python -m pytest state_paths/tests/ -q` — all pass (proves the sandbox resolves from the new location).
- `check_doc_budget`: run it — it should read the configured plan via `config/dev-model.yaml`.
- Confirm the repo's CI/lint scope **skips** the kit files (or add a kit-dir exclude if lint is repo-wide).

## Step 5 — Record the friction (the flywheel's first turn)

Seed `friction-log.md`'s first dated entry with every adoption friction you hit — a
skill collision, a namespacing rewrite, a tracker mismatch, a CI-scope surprise, a
review-bot detection miss. Tag `[kit]` on anything that's a kit-side fix and open an
issue upstream. This first entry *is* Principle #2 in action.

## Step 6 — Summarize + hand off

Report what was **installed / skipped / config-pointed**, open a **draft PR**, and
suggest the operator's first `/session-start`. Leave the merge to the operator — an
adoption touches a lot of the repo and deserves a human review pass.
