# Adopt

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

Everything below copies **from** that checkout **into** the current repo (the adopter) —
**two trees, and from here every write must name which one.** Bind both roots now,
before the first write, and use them for the rest of the workflow:

```bash
REPO="$(git rev-parse --show-toplevel)"   # the repo being adopted into
KIT=/tmp/agentic-dev-kit                  # the kit checkout you are copying FROM
echo "REPO=$REPO"; echo "KIT=$KIT"; echo "pwd=$(pwd)"
```

**Check that output before continuing.** `$REPO` must be the repo you meant to adopt
into, and `pwd` must be inside it. This is the assertion, and it belongs *before* the
first write — after it, it is a post-mortem.

The hazard is that a `cd` into `$KIT` — to inspect the fetched kit, to read a file such
as `init.sh` for Step 1 below — **outlives the command that made it**, and every
relative path afterwards resolves in the clone. Two sessions lost time to exactly this
on 2026-08-09, and neither recognised it: one had `cp` and `./init.sh` land in the
verification clone and read it as filesystem corruption; the other ran greps in the
wrong tree and got a startling wrong answer it nearly believed. The failure mimics a
broken tool rather than a wrong directory, which is why the guard has to be structural
rather than attentive (`#399`).

When you verify a copy landed, **hash it at the destination** —
`shasum -a 256 "$REPO/<path>"` — rather than reading `git status` from wherever the
shell is. In the first occurrence above, the destination hash is what would have
revealed it, and `git status` is what concealed it.

## Step 1 — Inspect the target repo (read-only)

Run these probes and record the answers — they drive the plan:

- **Living plan?** `ls ROADMAP.md PLAN.md docs/plan.md docs/handoff.md handoff.md 2>/dev/null`. If one exists, the repo already practices Principle #1 — you'll point the kit at it, not add a second plan.
- **Skill collisions?** Inspect `.claude/commands/` and `.agents/skills/`. Which of the kit's workflows already exist for either runtime? Keep the adopter's implementation and install only the missing adapters.
- **Seedable targets?** Classify each of the **six** files `init.sh` can render over into one of **four** states. Presence alone is not enough. The six are `AGENTS.md`, `CLAUDE.md`, and the four narrative docs *at their configured paths* — read `seed_doc`'s call sites for the list (four for the narrative paths, two for the entry points) rather than a line number; the two ranges cited here were stale within a release of being written. Read them at the absolute path `"$KIT/init.sh"`. **Do not `cd "$KIT"` to get there** — Step 0 above names the hazard of a `cd` into the kit checkout outliving the command that made it; this file read is exactly the kind of "just quickly look" step that invites it. **All four narrative docs ship pre-marked** with `devkit-template: unrendered`, so a repo that took the `cp -r` quickstart has four marker-carrying files before it has any of its own; verified on the shipped copies of all four:

  **Read line 1 of each of the six yourself and report the state.** Do not run a shell
  snippet for this — the predicate belongs to `init.sh` (`_seedable`), and every attempt to
  restate it here diverged from it on some input: a locale-dependent `[[:space:]]`, a broken
  symlink read as absent, a `grep` for a configured path that resolved a decoy under an
  unrelated section. Read the four narrative paths out of `config/dev-model.yaml`'s `paths:`
  section — you can parse YAML; a `grep` for the key cannot tell which section it is in.

  | line 1 of the file | state | bare `init.sh` | `init.sh --no-clobber` |
  |---|---|---|---|
  | file absent | `ABSENT` | seeds it | seeds it |
  | a directory, or a **broken** symlink | `NOT_A_REGULAR_FILE` | leaves it, reports `already in use` | same |
  | opens `<!-- devkit-template: unrendered` or `<!-- devkit-source: kit-own`, marker first in the comment | `MARKED` | **renders over it, no backup** | leaves it, reports `left untouched (--no-clobber)` |
  | anything else | `IN_USE` | leaves it byte-identical | same |

  Step 3c hands the operator the right-hand column. Classify against the left one anyway:
  it is what they fall back to, and the difference between the columns is the whole reason
  a `MARKED` finding is worth reporting.

  Three traps, all of which have caught this repo before:

  - **The marker must be the first token of the comment.** `<!-- see the devkit-source:
    kit-own convention -->` is prose and is **not** marked; `devkit-source: kit-ownership`
    is a different string and is **not** marked either; a marker on line 2 does not count.
  - **An odd blank beside the marker means not-marked.** `init.sh` compares under `LC_ALL=C`,
    so an NBSP or other non-ASCII blank after the marker text fails to match and the file is
    left alone. If you see anything but a plain space or tab there, treat it as `IN_USE`.
  - **A *working* symlink is classified by its target, not by being a link.** `[ -f ]`
    follows it, so a link whose target opens with a marker is `MARKED` — a bare run then
    replaces the **link** with the rendered file (`mv`), reporting only `seeded`. The target
    keeps its bytes; what is lost is the link relationship. `--no-clobber` declines it like
    any other `MARKED` target, so the link survives. Do not bucket "it's a symlink" as
    `NOT_A_REGULAR_FILE`: only a *broken* one is. See `_seedable`'s own comments in
    `init.sh` for why this follows from the marker rule rather than being a separate one.

  The three traps above are not stylistic: each was a real defect here, found by executing
  rather than reading. The state names also match `init.sh`'s own `_seedable` exactly —
  differential-tested across `#288`'s full near-miss set (mid-comment substring,
  `kit-ownership` prefix, marker on line 2, `unrendered-ish` suffix, NBSP, CRLF, broken
  symlink, directory, empty file), 0 divergences. That agreement is what makes this step
  worth doing at all: if it disagreed with `_seedable`, it would be lying about what is
  about to happen to the file.

  **`MARKED` is the state that costs something, and it is not hypothetical.** A file whose
  first line carries a kit marker is *seedable*: a bare `init.sh` renders over it and
  reports only `seeded`, with **no backup**. Verified — an `AGENTS.md` opening with
  `<!-- devkit-source: kit-own -->` and carrying paragraphs of adopter doctrine below it
  was replaced wholesale, unrecoverably. That behaviour is correct for `init.sh` on a fresh
  repo or an upgrade, and it flatly contradicts this skill's "never overwrite an existing
  file" contract. The adopter who hits it took the pre-`#288` `cp -r` quickstart and then
  edited what landed — a shipped path, not an edge case.

  **The destruction is now handled mechanically and this classification is still what makes
  the outcome legible.** Step 3c hands the operator `./init.sh --no-clobber` (`#297`), which
  refuses to write any existing file and names each one it declined — so a wrong call here
  costs an unrendered skeleton and a second run, not a lost file. What the flag cannot do is
  say *which* it was: it sees the same line 1 for a pristine skeleton and for an adopter's
  own doctrine. That is what this classification tells them, and why it is still worth
  producing carefully.

  `/adopt` remains read-only about it: it does not gate, back up, restore, re-render, or run
  `init.sh`. That is a deliberate retreat — four mechanisms were built here to run `init.sh`
  safely (a backup-and-restore, a re-classify-and-diff, an advisory gate, a gate fused to
  the run) and every one shipped a new way to destroy an adopter's file. The mechanical fix
  belongs in `init.sh`, where a test holds it. Prose in a markdown file cannot: nothing
  executes it.

- **Config dir?** `ls -d config 2>/dev/null` — where `config/dev-model.yaml` goes (repo root if there's no `config/`).
- **`scripts/` layout?** `ls scripts 2>/dev/null`. **Default to vendoring the kit's engines under `scripts/devkit/`.** It is required when `scripts/` is organized into subdirs or has colliding filenames, and it is the right call anyway whenever the repo lints or formats repo-wide (next bullet) — a directory is the only unit you can exclude without maintaining a filename list. Flat `scripts/` is only appropriate for a repo with no repo-wide lint and no collisions.
- **Tracker?** `gh issue list -L1 2>/dev/null` succeeds → GitHub Issues; else look for a Linear/Jira setup. Sets `tracker.backend`.
- **Review bot?** Do NOT infer from a config file — a repo can have CodeRabbit/Bugbot enabled org-wide with no in-repo config. Check a recent PR or the org settings. Sets `review.bots`.
- **CI/lint scope?** Read `.pre-commit-config.yaml` + `.github/workflows/`. Does lint run repo-wide or scoped to a package dir? If **anything** lints or formats repo-wide, read [`adopting-into-a-linted-repo.md`](../adopting-into-a-linted-repo.md) before writing a single file, and plan the engines directory around it.

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
| — a `MARKED` target | e.g. `AGENTS.md` MARKED | **Name it in the plan and again in the Step 3c handoff.** Step 3c's `--no-clobber` leaves it alone and says so; the operator then deletes line 1 to keep the content permanently, or deletes the file to have it seeded. `/adopt` does neither on their behalf and does not run `init.sh` at all |
| pre-push hook | not installed | **installed when the operator runs `init.sh`** (Step 3c) — nothing else installs it, so if they skip that step the repo has no hook |
| tracker | e.g. GitHub Issues | `tracker.backend: github-issues` |
| review bot | e.g. CodeRabbit (org) | `review.bots: [coderabbit]` |

State the scripts placement, whether the repo's CI/lint needs a kit-dir exclude, and
that everything lands on a branch. **Do not proceed until the operator confirms.**

## Step 3 — Execute (on a branch, non-destructively)

Everything from here mutates the repo, so re-assert `$REPO` before the first write —
per **Working across two trees** in [`AGENTS.md`](../../../AGENTS.md):

```bash
cd "${REPO:?REPO is not set — re-run Step 0}" || exit 1
git checkout -b chore/adopt-agentic-dev-kit
```

Write it as `${REPO:?...}`, not bare `"$REPO"`. A bare `cd "$REPO"` with `$REPO` unset
or emptied — the exact case this guard exists for, a shell that never ran Step 0, or
ran it in a session that didn't survive to here — returns exit **0** and silently
leaves you wherever you already were; `cd ""` is a no-op success, not a failure, so
`|| exit 1` never fires (confirmed in both `bash` and `zsh`). `${REPO:?msg}` fails the
parameter expansion itself, before `cd` ever runs, so the guard actually stops the
branch checkout — and everything mutating after it — from landing wherever the shell
happens to be, instead of only stopping it when `$REPO` names a path that doesn't exist.

Every `$KIT` reference from here on carries the same failure mode and the same fix —
see Step 3b and Step 4 below, where it recurs on commands run later, possibly in a
different session than the one that bound it.

The paths below are named relative to `$REPO`, the destination bound in Step 0 —
resolve each one there rather than against `pwd`. Where a bullet also names a kit-side
source path, that is relative to `$KIT`; not every bullet has one — "Engine scripts"
below names only a destination convention (`scripts/devkit/`), because the kit itself
ships no matching source path to anchor. For each piece, **copy only if the target
doesn't already exist**:

- **Shared workflows** → `docs/agentic-dev-kit/workflows/`.
- **Runtime adapters** → `.claude/commands/` and `.agents/skills/` (skip any target that collides with an existing workflow).
- **Engine scripts** → `scripts/devkit/` (flat `scripts/` only under the Step-1 conditions). Set `paths.engines` to that directory; do not rewrite prompt files. The engines find the repo root by walking up for `.git`, which is unbounded, so any depth works in a real checkout. In a tree with **no `.git` at all** the two implementations differ: the *Python* engines (`scripts/lib/kitconfig.py`) fall back to depth arithmetic calibrated for `scripts/`, which resolves a vendored layout to the wrong directory — a known, deliberate limitation (issue #60). The *shell* engines have no fallback: `scripts/lib/repo_root.sh`'s `devkit_find_repo_root` just returns 1, and its callers exit — `scripts/dev_session.sh:65` prints `[dev-session] error: no .git repository found above …`, `scripts/reconcile_sessions.sh:54` the same with `[reconcile]`. Both fail loudly rather than guessing, by different routes.
- **Safety doctrine** → `docs/agentic-dev-kit/safety-critical-changes.md`; install the thin `.claude/rules/safety-critical-changes.md` adapter when absent and merge `docs/AGENTS-sections.md` into an existing `AGENTS.md` when applicable.
- **Lint-containment doctrine** → `docs/agentic-dev-kit/adopting-into-a-linted-repo.md`. Install it whenever Step 1 found repo-wide lint or format, and apply its exclusions **in the same commit as the engines** — an engine that gets autoformatted before the exclusion lands is already drifted. `kit_doctor` tracks this file, so skipping it shows up as a permanent `missing`.
- **`config/dev-model.yaml`** — stamp the Step-1 values: `paths.handoff` → the existing plan (and `paths.handoff_history` / the `doc_budgets` entry to match), `paths.engines`, `runtime`, `tracker`, `review`, `triage`, and `models`. Use the shipped flat `triage:` block; do not create a separate friction-triage config or duplicate `paths`, tracker, notification, state, branch, or model values beneath it. Refreshed `init.sh` adds missing triage keys section-scoped without replacing adopter values. **`review:` must exist as a key before the operator runs `init.sh`**, even if you only know `review.bots` — `init.sh` fills a *partial* `review:` section in completely, but cannot create one from nothing. It instead emits `could not add review.*` warnings for the missing `noise_markers`, `unavailable_markers`, `fallback_panel`, `informational_checks`, `require_ci`, `bot_pending_grace_minutes`, `bots`, and `bot_author_aliases` keys; the `runtime:` section has no such limitation, which is why this is easy to miss.
- **`docs/templates/`** — the six `.md.tmpl` files, **unless the Step-2 plan declined them**. They are **manifest-tracked**, so omitting them is not merely a missed convenience: `kit_doctor` then reports six extra `missing` entries tagged `[template]` (measured). Read that cost the right way round, because stated bare it pushes the wrong way: `missing` entries are the *expected* reporting shape for a piece the operator declined, and Step 3b records exactly those as `not_installed` so later runs say "intact for this adoption" rather than counting them forever. Six `missing` lines are not a reason to install six files the plan dropped — installing them to quiet the count converts a decision into an install, which is `#398`'s shape one workflow over. They are also what `init.sh` renders from when the operator runs it, so a repo whose narrative docs are all already in use needs them only if it wants future seeding.
- **`init.sh`** — copy it to the adopter root. It is manifest-**tracked** (`#362`), so it must be in place *before* Step 3b's `--record-install`, and `kit_doctor` reports drift on it afterwards — `STALE` once the kit moves on, `LOCALLY EDITED` if someone changes it. (This line used to say the opposite, and the instruction it produced was "don't check the installer" — the exact check `#360` was closed to make possible; `#382`.) **If the adopter already has a root `init.sh`, STOP.** The copy-only-if-absent rule would silently skip it, and Step 3c would then tell the operator to run *their* script — `init.sh` is a common name for an unrelated bootstrap. Diff the two, and let the operator choose: keep the kit's under another name and hand off that path explicitly, or confirm theirs is a stale kit copy safe to replace. Never hand off a bare `./init.sh` you did not put there.
- **The friction log (`paths.friction_log`)** — do not hand-copy it. `init.sh` seeds it from the template, at the configured path, when the operator runs it.
- **`config/*.local.yaml` → `.gitignore`**, now, by hand — the one `.gitignore` entry that cannot wait for `init.sh`. `kitconfig.load_config()` merges a gitignored `config/dev-model.local.yaml` over the tracked config, and `docs/getting-started.md` tells the operator to put their Slack DM id there. Anyone who creates that file before the operator runs `init.sh` — routine for someone who already knows the kit's local-override pattern — otherwise has an identity sitting untracked-but-not-ignored when the later PR opens. `init.sh` appends the full set later; this one entry is proactive because its pre-PR window is the hazard.
- Copy `PRINCIPLES.md`, `docs/parallel-dev.md`, and the shared workflow/safety docs under `docs/agentic-dev-kit/` for reference.

**Never overwrite an existing file.** If something you didn't anticipate collides, stop
and ask the operator.

### Step 3b — record the drift baseline

**Once every copy above is done, and before the Step 3c handoff:**

```bash
uv run <engines-dir>/kit_doctor.py --record-install --from-kit "${KIT:?KIT is not set — re-run Step 0}"
```

**`${KIT:?...}`, not bare `"$KIT"`, and this is not decoration — though the unguarded
failure is not the single crash it first looks like; it is two different failures
depending on when you hit it.** `--record-install` reads `<from_kit>/kit-manifest.json`
as its *source* whenever `--from-kit` is given at all, and refuses if that read fails —
it does not fall back to recording everything. On a genuine first adoption, where
`$REPO/kit-manifest.json` does not exist yet (this command is what creates it),
`--from-kit ""` actually **fails loudly**: `Path("").resolve()` is the current
directory, so it looks there for `kit-manifest.json`, finds nothing, and exits 2 with
`cannot read kit-manifest.json: No such file or directory` — a real failure, but a
**confusing** one that reads as a missing kit checkout, not an unset variable. The
dangerous branch is the one Step 4 below sends you back to on purpose ("re-run Step 3b's
`--record-install --from-kit` command above"): by then `$REPO/kit-manifest.json`
already exists from the first successful run, so `Path("").resolve()` silently finds
*that* file — this repo's own baseline — and treats it as the kit's, rewriting it
stamped with **this repo's own** `git HEAD` as `kit_commit`, with no warning. Measured
both ways, reproduced end to end each time. `${KIT:?msg}` fails the parameter expansion
itself, before `uv run` is even invoked, so an empty or unset `$KIT` fails **closed** in
both branches, instead of failing confusingly in one and silently wrong in the other.
This step is exactly the "different session, different day" case the variable is most
likely to have gone missing in, since it runs after every copy in Step 3 — bind `$KIT`
again from Step 0 if this fails.

Order matters for every manifest-tracked path: `docs/templates/` **and `init.sh`** (tracked
since `#362`) must be copied *before* this runs, or the baseline records them as not
installed. The operator's later `init.sh` run still does not disturb the baseline, but the
reason is no longer "`init.sh` is untracked" — it is that **`init.sh` never writes to
itself**, and what it does write (`AGENTS.md`, `CLAUDE.md`, `config/dev-model.yaml`, the
rendered narrative docs) is adopter-owned and manifest-untracked. So recording here, before
they run it, is correct and not a race.

> **If you kept the adopter's own root `init.sh`** (the STOP case above), expect this step
> to refuse it — a present kit-owned path that does not match the source kit is left out of
> the baseline by design. It currently takes the whole `not_installed` declaration with it,
> so every deliberately-declined file starts reporting as `missing` and the run exits 1.
> That is `#388`; until it is closed, re-add the declaration by hand rather than accepting
> a baseline that declares no scope.

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
any other edit to a file they own. `init.sh` is different — bare, it *renders over* any of six files whose first line
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
and this repo's `make test` passed in full without touching a line of it. **A
safety-critical guard cannot live in an untested medium.**

`#297` moved it to `init.sh`, where CI holds it: **`./init.sh --no-clobber` seeds only
genuinely-absent targets** and never writes an existing file, marker or no marker. Each one
it declines is reported as `left untouched (--no-clobber): <path>` and again in a summary
at the end of the run. That is the guarantee this step used to ask the operator to produce
by hand, and it is now the flag they are handed.

**Hand them the flag, always.** `/adopt` still does not run it — the run is interactive and
theirs — but the command they are given carries the guarantee rather than depending on
their reading of six line-1s.

**What the flag does not decide, and must not be described as deciding:** a marker means
the kit *may* own the file, not that the file is *still* the kit's. So `--no-clobber`
leaves a genuinely pristine skeleton unrendered too, and the operator finishes those by
hand. In an `/adopt` flow that is usually nothing — the narrative docs are seeded at
configured paths this skill deliberately does not hand-copy, so they are absent and get
seeded normally. It bites the adopter who took the `cp -r` quickstart, whose four narrative
docs are present-and-marked. Step 1's classification is what tells them which case they are
in; the flag is what makes guessing wrong survivable.

**Report to them, in these words:**

> The adoption is staged on this branch. The next step is `./init.sh --no-clobber`, and you
> should run it yourself so you see and confirm each prompt.
>
> **Run it with `--no-clobber`.** With that flag it writes only files that are genuinely
> missing — it will not render over anything already on disk, including the six paths it
> would otherwise claim by a marker on line 1 (`AGENTS.md`, `CLAUDE.md`, and your
> configured `paths.handoff`, `paths.handoff_history`, `paths.friction_log`,
> `paths.friction_log_archive`). Anything it declines is printed as
> `left untouched (--no-clobber): <path>` and listed again at the end of the run.
>
> Read that end-of-run list, because those files are the ones the run did not finish. For
> each: if it is an unrendered skeleton you want filled in, delete it and re-run; if it is
> yours, delete line 1 to claim it permanently, and it will never be a candidate again.
> Without the flag `init.sh` renders over every one of them with no backup, reporting only
> `seeded` — which is right for a fresh repo and wrong here.
>
> It seeds the docs and entry points that are **missing**, leaving every file already on
> disk byte-identical; installs the pre-push hook **unless a non-shim hook is already there**,
> in which case it says so and leaves yours alone; and appends the kit's `.gitignore`
> entries — all of them except `config/*.local.yaml`, which the adoption already added
> because it could not wait for this step. Nothing else in the adoption seeds a doc,
> installs the hook, or adds the rest of those ignores. Read what it prints — the
> conditionals above are reported per file.
>
> Once it has run, move the adoption-friction entries from this PR's body into the seeded
> `paths.friction_log` — they are in the PR because the file did not exist while the
> adoption was staged.

Do not open a pull request while this operator step is pending. When the operator
returns, resume at Step 4, verify and commit the resulting adoption, and only then
continue to the ready-for-review creation in Step 6. The work can be completed locally,
so creating a remote draft here would manufacture rather than contain the bounded
exception.

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

**These checks cover the staged adoption — the copies, config, and the operator's
completed Step 3c `init.sh` run. Verify that run from what it printed.**

- **After the operator has run `init.sh`, go through its output with them.** It reports
  every decision per file, so read it rather than re-deriving it:
  - `seeded <path>` — the file was missing, and now holds the template. (Without
    `--no-clobber` this also covers a file that existed and carried a marker, which is why
    Step 3c hands them the flag.)
  - `<path> already in use — left untouched` — it had content and no marker, and still has
    that content, byte for byte. Confirm each path named here is one you expected to keep.
  - `left untouched (--no-clobber): <path>` — it existed AND carried a marker, so the flag
    declined it. **These are the unfinished ones**, repeated in a summary at the end of the
    run. Go through that list with them: a pristine skeleton wants deleting and a re-run; a
    file of their own wants line 1 deleted so it is never a candidate again. An empty list
    here means the adoption seeded everything it needed to.
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
  tmp="$(mktemp -d)" && DEVKIT_STATE_ROOT="$tmp" uv run --with pytest --with pyyaml python -m pytest \
    scripts/devkit/lib/state_paths/tests/ scripts/devkit/tests/ -q
  ```

  (Adjust the prefix when engines live directly under `scripts/`.)

  **`DEVKIT_STATE_ROOT` is not optional, and the `&&` is what makes it fail
  closed.** `pr_watch.py` computes its persistence root once, at import time,
  resolving `$DEVKIT_STATE_ROOT`, then a `.devkit_state_root` marker, then
  `<repo>/state`. It is the only engine that reaches `state/` at all, and it
  resolves at import rather than per call — which is why an override has to
  be in the environment before the process starts. A fresh adoption has no marker, so absent the env var the
  third branch is what you get. `state/` may not exist yet at that point, but
  the very first run of this command is what creates it — without the
  override, that first run seeds live `state/pr-watch/` with fixture data (a
  fabricated review receipt, per `#428`) instead of leaving it for the first
  real PR the merge gate watches.

  Set it here even though `/adopt` is the path that *does* deliver the tests,
  and with them the `conftest.py` whose `_hermetic_state_root` fixture covers
  the same ground — that is `#132`'s point, and citing it for the opposite
  claim would get it backwards. Two reasons it still earns its place: the
  fixture protects a run of the suite, while the fail-closed form above
  protects against `mktemp` itself failing, which no fixture can; and an
  adopter who vendored selectively may have the tests without the conftest,
  since no test file is tracked by `kit-manifest.json` (`#40`).

  The two-step form is what makes the override fail closed, and `/upgrade`
  Step 5 carries the same idiom for the same reason: an inline
  `DEVKIT_STATE_ROOT=$(mktemp -d)` sets the empty string when `mktemp` fails,
  which the resolver reads as *no override* and answers with the repo
  default, so the failure lands the suite exactly where it must not go. `&&`
  gates the run on the assignment instead.
- `check_doc_budget`: run it — it should read the configured plan via `config/dev-model.yaml`.
- `kit_doctor`: run it **against `$KIT`'s manifest**, not bare:

  ```sh
  uv run <engines-dir>/kit_doctor.py --manifest "${KIT:?KIT is not set — re-run Step 0}/kit-manifest.json"
  ```

  Guarded the same way as Step 3b's `--from-kit`, for the same reason and for
  consistency — an empty `$KIT` here would resolve to the literal path
  `/kit-manifest.json` and fail anyway, but as an unrelated-looking "no such file"
  rather than a message that names the actual cause.

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
  operator, re-run Step 3b's `--record-install --from-kit` command above, then re-run
  `kit_doctor` and confirm the `intact` line appears. Leaving it means the adoption
  carries no declared scope at all, so every later `/upgrade` re-asks about every
  absent file — the conversation the declared set exists to end.

  **Then check the `baseline:` line by comparing the sha it prints**, not merely that it
  is present. It reports what the baseline *claims*, so a leftover baseline from an
  earlier attempt prints a real-looking line naming the wrong commit:

  ```sh
  git -C "${KIT:?KIT is not set — re-run Step 0}" rev-parse HEAD    # the baseline: line shows its first 12 chars
  ```

  Guarded for the same reason as the two commands above: `git -C ""` is not an error —
  git treats an empty `-C` argument as no `-C` at all and silently runs in whatever
  directory the shell is already in, printing *this repo's own* HEAD as if it were the
  kit's. That is the one failure this specific check exists to catch (a baseline naming
  the wrong commit), so an unguarded `$KIT` here can defeat the very check it is part
  of, and agree with a wrong Step 3b baseline instead of catching it.

  `baseline: none recorded` means Step 3b's `--record-install` did not run at all.
- Confirm the repo's CI/lint scope **skips** the kit files (or add a kit-dir exclude if lint is repo-wide).

## Step 5 — Record the friction (the flywheel's first turn)

Record every adoption friction you hit — a skill collision, a namespacing rewrite, a
tracker mismatch, a CI-scope surprise, a review-bot detection miss. Tag `[kit]` on
anything that's a kit-side fix and open an issue upstream. This *is* Principle #2 in
action.

Step 3c has now run. Write the entries directly into the resolved `paths.friction_log`
when that path is usable — whether `init.sh` seeded it or Step 1 classified the adopter's
file as `IN_USE`. If the entries were held temporarily in the PR body while Step 3c was
pending, move them now.

If the operator intentionally retained a `MARKED` friction-log path and no usable log
exists yet, keep the entries in the PR body, name that declined path in the final report,
and leave the explicit reconciliation step with the operator. Do not hand-write a
replacement: a markerless stub would become `IN_USE` and prevent a later `init.sh` run
from rendering the seeded structure.

## Step 6 — Summarize + hand off

Report what was **installed / skipped / config-pointed**, open the completed work as a
**ready-for-review PR**, and leave the merge to the operator — an adoption touches a lot
of the repo and deserves a human review pass. Ready status invites that review; it does
not authorize merge. Run `pr-watch --assert-ready` immediately after creation, before
its normal watch-and-fix loop. This handoff happens only after the operator completed
Step 3c, the adoption was verified, and the changes and PR body are complete, so the
material unfinished-work exception in `pr-watch` does not apply.

The final report names the resolved seedable paths, what `init.sh --no-clobber` actually
did to each, any `MARKED` path the operator intentionally retained, and the PR URL. Leave
`/session-start` (Claude) or `$session-start` (Codex) as the adopter's next step after
merge. If Step 3c is still pending, stop there instead: do not open or describe the
adoption as review-ready.
