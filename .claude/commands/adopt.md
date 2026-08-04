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
- **Seedable targets?** Classify each of the **six** files `init.sh` can render over into one of **four** states. Presence alone is not enough, and a wrong call here destroys files. The six are `AGENTS.md`, `CLAUDE.md`, and the four narrative docs *at their configured paths* (`init.sh:1260-1275`) — not just the two entry points, because the `cp -r` quickstart lands `docs/handoff.md` and `docs/friction-log.md` pre-marked, making those the likeliest to carry a marker:

  ```sh
  cfg=config/dev-model.yaml
  val() { v=$(grep -E "^[[:space:]]+$1:" "$cfg" | head -1 | awk '{print $2}' | tr -d "\"'"); \
          [ -n "$v" ] && printf '%s\n' "$v" || printf '%s\n' "$2"; }
  printf '%s\n' "AGENTS.md
  CLAUDE.md
  $(val handoff docs/handoff.md)
  $(val handoff_history docs/handoff-history.md)
  $(val friction_log docs/friction-log.md)
  $(val friction_log_archive docs/friction-log-archive.md)" | while read -r f; do
    [ -n "$f" ] || continue
    if   [ ! -e "$f" ] && [ ! -L "$f" ]; then s="ABSENT — init.sh will seed it"
    elif [ ! -f "$f" ];                  then s="NOT_A_REGULAR_FILE — not seedable; resolve by hand"
    elif head -n 1 "$f" | LC_ALL=C sed -n 's/^<!--[[:space:]]*//p' \
         | LC_ALL=C grep -qE '^(devkit-template: unrendered|devkit-source: kit-own)([[:space:]]|$)'
    then s="MARKED — init.sh WILL RENDER OVER IT (tell the operator, Step 3b)"
    else s="IN_USE — init.sh leaves it byte-identical"
    fi
    printf '%s: %s\n' "$f" "$s"
  done
  ```

  Three details in that snippet are load-bearing, each for a reason that already cost this
  repo a defect:

  - **`LC_ALL=C` on the `grep`, not only the `sed`.** `[[:space:]]` is locale-dependent,
    and `init.sh`'s `_opens_with_marker` pins `LC_ALL=C` for exactly this. Unpinned, an
    NBSP in the marker line — routine when text is pasted from a rich-text source — makes
    this report `MARKED` while `init.sh` leaves the file untouched. Reproduced.
  - **`[ ! -e ] && [ ! -L ]` for `ABSENT`.** `-e` alone is false for a *broken symlink*,
    which would then read as `ABSENT — will be seeded`; `init.sh` requires a regular file
    and leaves it alone. Same for a directory named `AGENTS.md`, which is `#288`'s round-3
    defect. Neither is seedable, so both get their own state rather than a wrong one.
  - **The labels match `init.sh`'s own `_seedable`.** Verified across the marker forms and
    `#288`'s full near-miss set — mid-comment substring, `kit-ownership` prefix, marker on
    line 2, `unrendered-ish` suffix, NBSP, broken symlink, directory. A divergence here
    would mean this step lies about what is about to happen to the file.

  **`MARKED` is the dangerous state, it is not hypothetical, and this skill will not
  work around it.** A file whose first line carries a kit marker is *seedable*: `init.sh`
  renders over it and reports only `seeded`, with **no backup**. Verified — an `AGENTS.md`
  opening with `<!-- devkit-source: kit-own -->` and carrying paragraphs of adopter
  doctrine below it was replaced wholesale, unrecoverably. That behaviour is correct for
  `init.sh` on a fresh repo or an upgrade, and it flatly contradicts this skill's "never
  overwrite an existing file" contract. The adopter who hits it took the pre-`#288`
  `cp -r` quickstart and then edited what landed — a shipped path, not an edge case.

  **This classification is the single most useful thing `/adopt` produces**, and it is all
  it does about the hazard: it is read-only, it is advisory, and it goes to the operator in
  Step 3b, who runs `init.sh` themselves. `/adopt` does not gate, back up, restore, or
  re-render anything.

  That is a deliberate retreat. Four mechanisms were built here to run `init.sh` safely — a
  backup-and-restore, a re-classify-and-diff, an advisory gate, a gate fused to the run —
  and every one shipped a new way to destroy an adopter's file. The mechanical fix belongs
  in `init.sh` (a no-clobber mode, `#297`), where a test can hold it. Prose in a markdown
  file cannot: nothing executes it.

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
| Root entry points | e.g. `AGENTS.md` ABSENT, `CLAUDE.md` IN_USE | **seed the absent one** from `docs/templates/` via `init.sh`; an IN_USE one is left byte-identical |
| — a `MARKED` target | e.g. `AGENTS.md` MARKED | **Name it in the plan and again in the Step 3b handoff.** The operator deletes line 1 themselves to keep the content, or lets `init.sh` render over it. `/adopt` does neither on their behalf and does not run `init.sh` at all |
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
- **Engine scripts** → `scripts/devkit/` (flat `scripts/` only under the Step-1 conditions). Set `paths.engines` to that directory; do not rewrite prompt files. The engines find the repo root by walking up for `.git`, which is unbounded, so any depth works in a real checkout. In a tree with **no `.git` at all** the two implementations differ: the *Python* engines (`scripts/lib/kitconfig.py`) fall back to depth arithmetic calibrated for `scripts/`, which resolves a vendored layout to the wrong directory — a known, deliberate limitation (issue #60). The *shell* engines (`scripts/lib/repo_root.sh`) have no fallback and exit with `error: no .git repository found above …`. Both fail loudly rather than guessing, by different routes.
- **Safety doctrine** → `docs/agentic-dev-kit/safety-critical-changes.md`; install the thin `.claude/rules/safety-critical-changes.md` adapter when absent and merge `docs/AGENTS-sections.md` into an existing `AGENTS.md` when applicable.
- **Lint-containment doctrine** → `docs/agentic-dev-kit/adopting-into-a-linted-repo.md`. Install it whenever Step 1 found repo-wide lint or format, and apply its exclusions **in the same commit as the engines** — an engine that gets autoformatted before the exclusion lands is already drifted. `kit_doctor` tracks this file, so skipping it shows up as a permanent `missing`.
- **`config/dev-model.yaml`** — stamp the Step-1 values: `paths.handoff` → the existing plan (and `paths.handoff_history` / the `doc_budgets` entry to match), `paths.engines`, `runtime`, `tracker`, `review`, and `models`. **`review:` must exist as a key before the operator runs `init.sh`**, even if you only know `review.bots` — `init.sh` fills a *partial* `review:` section in completely, but cannot create one from nothing and emits seven `could not add review.*` warnings instead (measured; the `runtime:` section has no such limitation, which is why this is easy to miss).
- **`docs/templates/`** — all six `.md.tmpl` files. They are **manifest-tracked**, so omitting them is not merely a missed convenience: `kit_doctor` then reports six extra `missing` entries tagged `[template]` (measured), and Step 4 tells you to expect `missing` only for pieces Step 2 deliberately dropped. They are also what `init.sh` renders from when the operator runs it.
- **`init.sh`** — copy it to the adopter root. It is manifest-*untracked*, so it does not affect the baseline. The operator runs it (Step 3b).
- **`friction-log.md`** — do not hand-copy it. `init.sh` seeds it from the template when the operator runs it, at the configured `paths.friction_log`.
- Copy `PRINCIPLES.md`, `docs/parallel-dev.md`, and the shared workflow/safety docs under `docs/agentic-dev-kit/` for reference.

**Never overwrite an existing file.** If something you didn't anticipate collides, stop
and ask the operator.

### Step 3b — hand `init.sh` to the operator, and stop

**`/adopt` does not run `init.sh`. This is the end of what the skill does to the repo.**

Everything up to here is additive: files copied into paths that were empty, and a config
stamped. `init.sh` is different — it *renders over* any of six files whose first line
carries a kit marker, with no backup, reporting only `seeded`. That is correct behaviour
for `init.sh`, and it is the opposite of this skill's contract.

Four attempts were made to run it safely from here: a backup-and-restore around it, then a
re-classify-and-diff, then an advisory gate, then a gate fused to the run. Each was
reviewed, each shipped a new way to destroy an adopter's file, and the last one's own fix
contained three fresh defects that four independent reviewers had not seen — because a
shell snippet in a markdown file is executed by nobody: no test runs it, no linter checks
it, and this repo's `make test` passes 837 tests without touching a line of it. **A
safety-critical guard cannot live in an untested medium.** `#297` moves it to `init.sh`,
where CI can hold it.

So: tell the operator what to check, and let them run it.

**Report to them, in these words:**

> The adoption is staged on this branch. The last step is `./init.sh`, and you should run
> it yourself because it can overwrite files.
>
> `init.sh` renders a template over any of these six paths whose **first line** opens an
> HTML comment beginning `devkit-template: unrendered` or `devkit-source: kit-own` —
> `AGENTS.md`, `CLAUDE.md`, and your configured `paths.handoff`, `paths.handoff_history`,
> `paths.friction_log`, `paths.friction_log_archive`. There is no backup and the run
> reports only `seeded`.
>
> Open each of those six and look at line 1. If any carries one of those markers **and you
> want what is in the file**, delete line 1 first — that is how the kit records that the
> file is yours, and `init.sh` will then leave it byte-identical. If a marked file is just
> an unrendered skeleton, leave it and let `init.sh` fill it in.
>
> Then run `./init.sh` — interactively, so you see and confirm each prompt. It seeds the
> missing docs and both entry points, installs the pre-push hook, and appends the kit's
> `.gitignore` entries. Nothing else in this adoption does those things.

State the six paths **resolved from their config**, not as the defaults above, and say
which ones Step 1 found carrying a marker. That is the whole value `/adopt` adds here: it
knows where to look and what it found, and the operator makes the call.

Two things to warn them about, both measured, because neither is obvious from the output:

- If `tracker.project_name` contains a `/` and does not appear in this repo's `origin`
  URL, a **non-interactive** run exits 1 with `error: non-interactive run would keep
  tracker.project_name = …` before seeding anything — though *after* migrating the config.
  Running interactively avoids it.
- A `review:` key must already exist in the config, even with only `review.bots` under it.
  `init.sh` fills a partial `review:` section completely but cannot create one from
  nothing, and emits seven `could not add review.*` warnings instead. Step 3 stamps it.


### Step 3c — record the drift baseline

**Last, once every copy above is done — and before handing off to Step 3b:**

```bash
uv run <engines-dir>/kit_doctor.py --record-install --from-kit <kit checkout>
```

Order matters in one direction only: `docs/templates/` is manifest-tracked and must be
copied *before* this runs. The operator's later `init.sh` run does not disturb the
baseline — `AGENTS.md`, `CLAUDE.md`, `init.sh` and `config/dev-model.yaml` are all
manifest-untracked, the rendered entry points because they are adopter-owned and meant to
be edited. So recording here, before they run it, is correct and not a race.

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

**Steps 4a and 4b below verify the staged adoption — the copies and the config. They do
not verify `init.sh`, which the operator runs after this (Step 3b) and verifies for
themselves from what it prints.**

- **Entry points** — only meaningful *after* the operator has run `init.sh`, so run it
  with them rather than reporting it as done:

  ```sh
  for f in AGENTS.md CLAUDE.md; do
    [ -f "$f" ] && echo "$f: $(grep -c '{{[A-Z_]*}}' "$f") unsubstituted tokens (want 0)"
  done
  ```

  A non-zero count means the file was *copied* rather than rendered — what happens if
  someone substitutes `cp` for `init.sh`. There is deliberately nothing here that claims to
  prove a file was not clobbered: `/adopt` no longer runs the thing that could clobber it,
  and a stronger claim would need `#297`'s no-clobber mode, not another snippet in a
  markdown file that nothing executes.

- **Hook** — *only after the operator has run `init.sh`*; nothing in `/adopt` installs it.
  Resolve the directory the way `init.sh` does. `core.hooksPath` wins over
  `.git/hooks` when set (pre-commit and several monorepo setups set it), so checking
  `.git/hooks/pre-push` can inspect a file git will never run — or miss the one it will:

  ```sh
  hookdir="$(git config --get core.hooksPath || git rev-parse --git-path hooks)"
  grep -l devkit-hook-shim "$hookdir/pre-push"   # it is the kit's shim, not a stray hook
  # strip surrounding quotes: `engines: "scripts/devkit"` is ordinary YAML, and an
  # unstripped quote makes the match below fail on a correctly-installed hook
  eng="$(grep -E '^[[:space:]]+engines:' config/dev-model.yaml | awk '{print $2}' | tr -d "\"'")"
  grep -o "$eng" "$hookdir/pre-push"             # and it targets the engines dir you chose
  ```

  `init.sh` refuses to replace a **non-shim** hook already at that path — it prints
  `note: existing <path> left untouched (not a kit shim) — chain it to <src> by hand` and
  moves on. That is the right call, and it means a repo with its own `pre-push` finishes
  this step with the kit's hook **not installed**. Read for that line and chain it, rather
  than assuming the hook is live because Step 3b exited 0.

  **Verify the hook by making it fire, not by looking at it.** A shim that exists, is
  executable and names the right target can still be inert. Feed it a synthetic ref on
  stdin and confirm it refuses:

  ```sh
  pre="$(grep -E '^[[:space:]]+dev_branch_prefix:' config/dev-model.yaml \
         | awk '{print $2}' | tr -d "\"'")"
  zero=0000000000000000000000000000000000000000
  printf 'refs/heads/%s/probe %s refs/heads/%s/probe %s\n' \
    "$pre" "$(git rev-parse HEAD)" "$pre" "$zero" \
    | "$hookdir/pre-push" origin https://example.invalid
  echo "exit=$?"
  ```

  That probe uses `HEAD`, so it only *fires* when the current branch's diff against
  `origin/<protected_branch>` touches a narrative file. To prove the refusal path itself
  on any branch, build a throwaway commit that does — with plumbing, so nothing in the
  working tree or on any branch changes:

  ```sh
  b=$(printf 'probe\n' | git hash-object -w --stdin)
  idx=/tmp/adopt-probe.idx        # any path OUTSIDE the repo; a temp index, not a commit
  GIT_INDEX_FILE=$idx git read-tree origin/main
  GIT_INDEX_FILE=$idx git update-index --add --cacheinfo 100644,$b,<your handoff path>
  probe=$(git commit-tree "$(GIT_INDEX_FILE=$idx git write-tree)" -p origin/main -m probe)
  ```

  Feed `$probe` as the sha in the `printf` above. Exit 1 with the refusal message is the
  hook working.

  A non-zero exit with the refusal message is the hook working. Exit 0 means it did not
  fire — and note the guard **fails open by design** when it cannot resolve
  `origin/<protected_branch>`, so exit 0 on a fresh clone with no fetched remote is
  expected rather than broken.
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

  Bare, it compares this repo against the baseline Step 3c just wrote from these same
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

  `baseline: none recorded` means Step 3c's `--record-install` did not run at all.
- Confirm the repo's CI/lint scope **skips** the kit files (or add a kit-dir exclude if lint is repo-wide).

## Step 5 — Record the friction (the flywheel's first turn)

Seed `friction-log.md`'s first dated entry with every adoption friction you hit — a
skill collision, a namespacing rewrite, a tracker mismatch, a CI-scope surprise, a
review-bot detection miss. Tag `[kit]` on anything that's a kit-side fix and open an
issue upstream. This first entry *is* Principle #2 in action.

## Step 6 — Summarize + hand off

Report what was **installed / skipped / config-pointed**, open a **draft PR**, and
leave the merge to the operator — an adoption touches a lot of the repo and deserves a
human review pass.

**Then repeat Step 3b's handoff as the last thing you say**, because it is the one action
still outstanding and the adoption is not finished without it:

1. the six seedable paths, resolved from *their* config, with the state Step 1 found for
   each — and any `MARKED` one named explicitly, with what deleting line 1 does
2. `./init.sh`, run by them, interactively
3. `/session-start` (Claude) or `$session-start` (Codex) afterwards

Do not describe the adoption as complete before they have run `init.sh`: until then the
repo has no entry points, no pre-push hook, and no kit `.gitignore` entries.
