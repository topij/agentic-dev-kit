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
- **Seedable targets?** Classify each of the **six** files `init.sh` can render over into one of **four** states. Presence alone is not enough, and a wrong call here destroys files. The six are `AGENTS.md`, `CLAUDE.md`, and the four narrative docs *at their configured paths* (`init.sh:1260-1263` for the four, `:1274-1275` for the entry points) — not just the two entry points. **All four narrative docs ship pre-marked** with `devkit-template: unrendered`, so a repo that took the `cp -r` quickstart has four marker-carrying files before it has any of its own; verified on the shipped copies of all four:

  **Read line 1 of each of the six yourself and report the state.** Do not run a shell
  snippet for this — the predicate belongs to `init.sh` (`_seedable`), and every attempt to
  restate it here diverged from it on some input: a locale-dependent `[[:space:]]`, a broken
  symlink read as absent, a `grep` for a configured path that resolved a decoy under an
  unrelated section. Read the four narrative paths out of `config/dev-model.yaml`'s `paths:`
  section — you can parse YAML; a `grep` for the key cannot tell which section it is in.

  | line 1 of the file | state | what `init.sh` does |
  |---|---|---|
  | file absent | `ABSENT` | seeds it |
  | a directory, or a **broken** symlink | `NOT_A_REGULAR_FILE` | leaves it, reports `already in use` |
  | opens `<!-- devkit-template: unrendered` or `<!-- devkit-source: kit-own`, marker first in the comment | `MARKED` | **renders over it, no backup** |
  | anything else | `IN_USE` | leaves it byte-identical |

  Three traps, all of which have caught this repo before:

  - **The marker must be the first token of the comment.** `<!-- see the devkit-source:
    kit-own convention -->` is prose and is **not** marked; `devkit-source: kit-ownership`
    is a different string and is **not** marked either; a marker on line 2 does not count.
  - **An odd blank beside the marker means not-marked.** `init.sh` compares under `LC_ALL=C`,
    so an NBSP or other non-ASCII blank after the marker text fails to match and the file is
    left alone. If you see anything but a plain space or tab there, treat it as `IN_USE`.
  - **A *working* symlink is classified by its target, not by being a link.** `[ -f ]`
    follows it, so a link whose target opens with a marker is `MARKED` and `init.sh` renders
    over it — `mv` then replaces the **link** with the rendered file. The target keeps its
    bytes; what is lost is the link relationship, and the run reports only `seeded`
    (`init.sh:907-913`). Do not bucket "it's a symlink" as `NOT_A_REGULAR_FILE`: only a
    *broken* one is.

  The three traps above are not stylistic: each was a real defect here, found by executing
  rather than reading. The state names also match `init.sh`'s own `_seedable` exactly —
  differential-tested across `#288`'s full near-miss set (mid-comment substring,
  `kit-ownership` prefix, marker on line 2, `unrendered-ish` suffix, NBSP, CRLF, broken
  symlink, directory, empty file), 0 divergences. That agreement is what makes this step
  worth doing at all: if it disagreed with `_seedable`, it would be lying about what is
  about to happen to the file.

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
  Step 3c, who runs `init.sh` themselves. `/adopt` does not gate, back up, restore, or
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
| friction-log (#2) | none | **seeded by `init.sh`**, which the operator runs (Step 3c) — not by `/adopt` |
| parallel + `state_paths` (#3) | none | **install** under `scripts/devkit/` (see Step 1 on when flat `scripts/` is acceptable) |
| `pr-watch` (#5), safety rule (#6) | none | **install** |
| Root entry points | e.g. `AGENTS.md` ABSENT, `CLAUDE.md` IN_USE | **the absent one gets seeded** from `docs/templates/` when **the operator runs `init.sh`** (Step 3c) — not by `/adopt`; an IN_USE one is left byte-identical |
| — a `MARKED` target | e.g. `AGENTS.md` MARKED | **Name it in the plan and again in the Step 3c handoff.** The operator deletes line 1 themselves to keep the content, or lets `init.sh` render over it. `/adopt` does neither on their behalf and does not run `init.sh` at all |
| pre-push hook | not installed | **installed when the operator runs `init.sh`** (Step 3c) — nothing else installs it, so if they skip that step the repo has no hook |
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
- **Engine scripts** → `scripts/devkit/` (flat `scripts/` only under the Step-1 conditions). Set `paths.engines` to that directory; do not rewrite prompt files. The engines find the repo root by walking up for `.git`, which is unbounded, so any depth works in a real checkout. In a tree with **no `.git` at all** the two implementations differ: the *Python* engines (`scripts/lib/kitconfig.py`) fall back to depth arithmetic calibrated for `scripts/`, which resolves a vendored layout to the wrong directory — a known, deliberate limitation (issue #60). The *shell* engines have no fallback: `scripts/lib/repo_root.sh`'s `devkit_find_repo_root` just returns 1, and its callers exit — `scripts/dev_session.sh:65` prints `[dev-session] error: no .git repository found above …`, `scripts/reconcile_sessions.sh:54` the same with `[reconcile]`. Both fail loudly rather than guessing, by different routes.
- **Safety doctrine** → `docs/agentic-dev-kit/safety-critical-changes.md`; install the thin `.claude/rules/safety-critical-changes.md` adapter when absent and merge `docs/AGENTS-sections.md` into an existing `AGENTS.md` when applicable.
- **Lint-containment doctrine** → `docs/agentic-dev-kit/adopting-into-a-linted-repo.md`. Install it whenever Step 1 found repo-wide lint or format, and apply its exclusions **in the same commit as the engines** — an engine that gets autoformatted before the exclusion lands is already drifted. `kit_doctor` tracks this file, so skipping it shows up as a permanent `missing`.
- **`config/dev-model.yaml`** — stamp the Step-1 values: `paths.handoff` → the existing plan (and `paths.handoff_history` / the `doc_budgets` entry to match), `paths.engines`, `runtime`, `tracker`, `review`, and `models`. **`review:` must exist as a key before the operator runs `init.sh`**, even if you only know `review.bots` — `init.sh` fills a *partial* `review:` section in completely, but cannot create one from nothing and emits seven `could not add review.*` warnings instead (measured; the `runtime:` section has no such limitation, which is why this is easy to miss).
- **`docs/templates/`** — all six `.md.tmpl` files. They are **manifest-tracked**, so omitting them is not merely a missed convenience: `kit_doctor` then reports six extra `missing` entries tagged `[template]` (measured), and Step 4 tells you to expect `missing` only for pieces Step 2 deliberately dropped. They are also what `init.sh` renders from when the operator runs it.
- **`init.sh`** — copy it to the adopter root. It is manifest-*untracked*, so it does not affect the baseline. **If the adopter already has a root `init.sh`, STOP.** The copy-only-if-absent rule would silently skip it, and Step 3c would then tell the operator to run *their* script — `init.sh` is a common name for an unrelated bootstrap. Diff the two, and let the operator choose: keep the kit's under another name and hand off that path explicitly, or confirm theirs is a stale kit copy safe to replace. Never hand off a bare `./init.sh` you did not put there.
- **The friction log (`paths.friction_log`)** — do not hand-copy it. `init.sh` seeds it from the template, at the configured path, when the operator runs it.
- **`config/*.local.yaml` → `.gitignore`**, now, by hand — the one `.gitignore` entry that cannot wait for `init.sh`. `kitconfig.load_config()` merges a gitignored `config/dev-model.local.yaml` over the tracked config, and `docs/getting-started.md` tells the operator to put their Slack DM id there. Step 6 opens the PR *before* the operator runs `init.sh` (Step 3c), so anyone who creates that file in the gap — routine for someone who already knows the kit's local-override pattern — has an identity sitting untracked-but-not-ignored in an open PR. `init.sh` appends the full set later; this one entry is proactive because its window is the hazard.
- Copy `PRINCIPLES.md`, `docs/parallel-dev.md`, and the shared workflow/safety docs under `docs/agentic-dev-kit/` for reference.

**Never overwrite an existing file.** If something you didn't anticipate collides, stop
and ask the operator.

### Step 3b — record the drift baseline

**Once every copy above is done, and before the Step 3c handoff:**

```bash
uv run <engines-dir>/kit_doctor.py --record-install --from-kit <kit checkout>
```

Order matters in one direction only: `docs/templates/` is manifest-tracked and must be
copied *before* this runs. The operator's later `init.sh` run does not disturb the
baseline — `AGENTS.md`, `CLAUDE.md`, `init.sh` and `config/dev-model.yaml` are all
manifest-untracked, the rendered entry points because they are adopter-owned and meant to
be edited. So recording here, before they run it, is correct and not a race.

This writes `kit-manifest.json` here, recording which kit-owned files this adoption
actually installed — and, as `not_installed`, the ones it deliberately did not — plus the
kit commit they came from. It is what lets a later
`/upgrade` tell a **stale** file from a **hand-edited** one instead of guessing — the
guess was wrong for the commonest case and told adopters to hunt for edits they never
made (kit `#51`). The `not_installed` half does the same job one axis over: a **sized-down adoption
is a supported state**, and recording it here is what lets `kit_doctor` later say "intact
for this adoption" instead of reporting the same permanent count of absent files at every
run, with a real deletion indistinguishable inside it (#286).

**So a sized-down `/adopt` must still run this**, and against the full component list —
the value is in what it records as *declined*, which is precisely the part a partial
install would otherwise leave unstated. Do not skip it on the grounds that few files were
copied; that is the case it helps most.

Run it **after** the copies, so it records what landed: the subset this adoption
installed, and the rest as declined.

**Pass `--from-kit`, and read what it prints.** With it, only files matching that
checkout are recorded — which is what keeps the "copy only if the target doesn't already
exist" rule above from backfiring. A file this adoption *retained* rather than copied
(an adopter's own file already sitting at a kit-owned path) is not the kit's, and
recording it would make the next `/upgrade` report it `STALE` — wording that says
"replace them, nothing local is lost" about a file that is entirely theirs. Any such
path is named on stderr and left out of the baseline; reconcile each with the operator
before re-running, and never silence it by dropping the flag.

### Step 3c — hand `init.sh` to the operator, and stop

**`/adopt` does not run `init.sh`. This is the end of what the skill does to the repo.**

Everything up to here is **additive in the sense that nothing existing is removed or
rewritten**: files copied into paths that were empty, a config stamped, and lines appended
to files the repo already had — a `.gitignore` entry, a lint exclusion. One step goes
further and merges content: `docs/AGENTS-sections.md` into an existing `AGENTS.md`, which
interleaves with their prose rather than appending to it, and is theirs to approve like
any other edit to a file they own. `init.sh` is different — it *renders over* any of six files whose first line
carries a kit marker, with no backup, reporting only `seeded`. That is correct behaviour
for `init.sh`, and it is the opposite of this skill's contract.

Four attempts were made to run it safely from here: a backup-and-restore around it, then a
re-classify-and-diff, then an advisory gate, then a gate fused to the run. Each was
reviewed, each shipped a new way to destroy an adopter's file, and the last one's own fix
contained three fresh defects — found not by any reviewer but by extracting the shipping
snippet and running it. (No reviewer had *seen* that code: it was written after their
pass. That is the point rather than a criticism of them — a fix round's own output gets
reviewed only if someone reviews again, and here only execution caught it.) A shell
snippet in a markdown file is executed by nobody: no test runs it, no linter checks it,
and this repo's `make test` passes 837 tests without touching a line of it. **A
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
> docs and entry points that are **missing or unrendered**, leaving anything in use
> byte-identical; installs the pre-push hook **unless a non-shim hook is already there**,
> in which case it says so and leaves yours alone; and appends the kit's `.gitignore`
> entries — all of them except `config/*.local.yaml`, which the adoption already added
> because it could not wait for this step. Nothing else in the adoption seeds a doc,
> installs the hook, or adds the rest of those ignores. Read what it prints — the
> conditionals above are reported per file.
>
> Once it has run, move the adoption-friction entries from this PR's body into the seeded
> `paths.friction_log` — they are in the PR because the file did not exist while the
> adoption was staged.

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


## Step 4 — Verify

**These checks cover the staged adoption — the copies and the config. They do not cover
`init.sh`, which the operator runs afterwards (Step 3c) and verifies from what it prints.**

- **After the operator has run `init.sh`, go through its output with them.** It reports
  every decision per file, so read it rather than re-deriving it:
  - `seeded <path>` — the file was missing or unrendered, and now holds the template.
  - `<path> already in use — left untouched` — it had content, and still does, byte for
    byte. Confirm each path named here is one you expected to keep.
  - `note: existing <path> left untouched (not a kit shim) — chain it to <src> by hand` —
    the repo had its own `pre-push`, so **the kit's hook is not installed**. This is the
    one outcome that silently leaves a mechanism absent; chain it.
  - `note: CLAUDE.md does not import AGENTS.md, and Claude Code reads CLAUDE.md only.` —
    the two runtimes will read different
    contracts. Raise it; never edit their file to fix it.
  - `installed <hookdir>/<hook> -> <src>` — the hook is in place, at the directory
    `core.hooksPath` selects, which is not always `.git/hooks`.

  Then have them confirm one thing the output cannot show: that any file they chose to keep
  still reads the way they expect. `init.sh` reports what it *did*, which is not the same as
  what they *wanted*.

  There is deliberately no verification snippet here. Every one this document shipped was
  wrong on some input — a token count that read a destroyed file as clean, a hook check that
  called any non-zero exit a pass, a `mktemp` that is BSD-only and silently built an
  empty-tree probe on Linux. None of them were executed by any test. The checks worth having
  belong in `init.sh` and `kit_doctor`, where CI runs them; `#297` carries that.

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

  Bare, it compares this repo against the baseline Step 3b just wrote from these same
  files, so every recorded file matches *by construction* and the check establishes
  nothing — it would pass over a file that was copied wrong. The kit's manifest is an
  independent reference, and it is also the only one carrying `required_by`, which is
  what makes the `missing-required` axis work at all.

  Expect zero mismatches. **Not `missing` — Step 3b just recorded a declared install
  set**, so the pieces Step 2 deliberately left out now report as `declined` and the
  count line reads `0 missing` followed by `✓ intact for this adoption — N file(s)
  declined`. A surviving `missing` count means `--record-install` did not run, or ran
  against a different root. Zero `removed` and zero `new-upstream` too: on a fresh
  adoption there is nothing yet to have been deleted, and nothing the kit could have
  added since a baseline written minutes ago.

  If Step 3b reported unverified paths, there is **no** declared set — it suppresses one
  rather than record a partial claim, for **every** file rather than just the unverified
  ones — so the absences read `missing` here and the `intact` line is absent. That is the
  unreconciled-path signal, not a second failure.

  **It does not clear itself.** Reconcile each path Step 3b named on stderr with the
  operator, re-run `--record-install --from-kit <kit checkout>`, then re-run `kit_doctor`
  and confirm the `intact` line appears. Leaving it means the adoption carries no declared
  scope at all, so every later `/upgrade` re-asks about every absent file — the
  conversation the declared set exists to end.

  **Then check the `baseline:` line by comparing the sha it prints**, not merely that it
  is present. It reports what the baseline *claims*, so a leftover baseline from an
  earlier attempt prints a real-looking line naming the wrong commit:

  ```sh
  git -C <kit checkout> rev-parse HEAD    # the baseline: line shows its first 12 chars
  ```

  `baseline: none recorded` means Step 3b's `--record-install` did not run at all.
- Confirm the repo's CI/lint scope **skips** the kit files (or add a kit-dir exclude if lint is repo-wide).

## Step 5 — Record the friction (the flywheel's first turn)

Record every adoption friction you hit — a skill collision, a namespacing rewrite, a
tracker mismatch, a CI-scope surprise, a review-bot detection miss. Tag `[kit]` on
anything that's a kit-side fix and open an issue upstream. This *is* Principle #2 in
action.

**Put it in the PR body, not in the friction log.** At this point the friction log
usually does not exist: `/adopt` no longer creates it, and `init.sh` seeds it from the
template when the operator runs it — which is Step 3c, after everything here. Hand-writing
the file now would be actively harmful, not merely early: a hand-written file carries no
kit marker, so `_seedable` reads it as `IN_USE` and `init.sh` will *never* render the
template into it. You would permanently trade the seeded structure for a stub, through the
exact clobber-avoidance property this skill exists to preserve.

So: the entries go in the PR body, and the Step 3c handoff tells the operator to move them
into `paths.friction_log` once they have run `init.sh`. If the repo already *had* a friction
log (Step 1 classified it `IN_USE`), write to it directly — `init.sh` will leave it alone.

## Step 6 — Summarize + hand off

Report what was **installed / skipped / config-pointed**, open a **draft PR**, and
leave the merge to the operator — an adoption touches a lot of the repo and deserves a
human review pass.

**Then repeat Step 3c's handoff as the last thing you say**, because it is the one action
still outstanding and the adoption is not finished without it:

1. the six seedable paths, resolved from *their* config, with the state Step 1 found for
   each — and any `MARKED` one named explicitly, with what deleting line 1 does
2. `./init.sh`, run by them, interactively
3. `/session-start` (Claude) or `$session-start` (Codex) afterwards

Do not describe the adoption as complete before they have run `init.sh`: until then any
entry point they lacked is still missing, the pre-push hook is not installed, and the kit's
`.gitignore` entries are absent apart from the `config/*.local.yaml` line Step 3 added.
Say it that way rather than "the repo has no entry
points" — a repo with its own `AGENTS.md` has one, and `init.sh` will leave it alone.
