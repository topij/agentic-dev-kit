# Getting started

A worked example of one full session with the kit — from adoption through your
first `wrap-up` — so you can see the basic flow end to end. It assumes you drive
an AI coding agent that can run repository skills and shell
commands, on a repo that uses branches + pull requests with review before merge.

Workflow names are runtime-neutral below. Invoke them as `/name` in Claude Code or
`$name` in Codex.

The loop you're setting up:

> **`session-start` → work → `pr-watch` → `wrap-up`**, with the **friction
> flywheel** (`/triage-friction-log`, `/post-merge-systemize`) turning underneath.

See the [README diagram](../README.md#how-it-fits-together) for the whole picture.

**Prerequisites.** `init.sh` needs POSIX `sh` plus the usual coreutils/text tools it
shells out to — `awk`, `grep`, `sed`, `mv`, `rm`, `cat`, `head`, `mkdir`, `chmod`, `touch`,
`basename`, `dirname`, `date` and `git` — all standard on macOS
and Linux. The engines additionally need
[`uv`](https://docs.astral.sh/uv/) (they're PEP-723 single-file scripts) and, for
`pr-watch` / `parallel`, the GitHub CLI `gh`, authenticated (`gh auth status`). No
PyYAML — `kitconfig.py`, the config reader every engine imports, is stdlib-only.

## 1 · Adopt the kit

Click **Use this template** on GitHub and clone the result, or copy the kit's
contents into an existing repo's root:

```sh
cp -r /path/to/agentic-dev-kit/. .
./init.sh
```

> Already adopted the kit in this repo before? Don't repeat this from scratch —
> pull the new kit files and re-run `./init.sh`. See the README's
> [Upgrading an already-adopted repo](../README.md#upgrading-an-already-adopted-repo)
> section for what that does and doesn't touch.

`init.sh` prompts you for a handful of values — project name, agent runtime, tracker board,
the protected branch, your review bot — and stamps them into `config/dev-model.yaml`.
It renders the four narrative docs and both root entry points — `AGENTS.md`, which holds
the contract, and `CLAUDE.md`, which imports it with `@AGENTS.md` because Claude Code reads
`CLAUDE.md` and not `AGENTS.md` — from `docs/templates/`, installs the pre-push hook, and
adds the state sandbox to `.gitignore`.

It renders a target when it is **missing, or its first line opens an HTML comment
carrying one of two markers** — so a handoff you are actually using is left
byte-identical, which is what makes re-running it the supported upgrade path.

- `devkit-template: unrendered` marks a **shipped skeleton** — the four narrative docs.
- `devkit-source: kit-own` marks the **kit's own** root `AGENTS.md` and `CLAUDE.md`. The
  kit ships those two because a session working in the kit needs a contract too, and the
  `cp -r` quickstart therefore lands them in your root. This marker is what lets `init.sh`
  render yours over them instead of mistaking them for files you are already using.

A marker counts only in one exact position — line 1 must **open an HTML comment whose
first words are the marker**:

```markdown
<!-- devkit-source: kit-own — anything may follow -->
```

A comment that merely *talks about* a marker does not qualify, wherever it sits:
`<!-- see the kit's devkit-source: kit-own convention -->` on line 1 is in use, and seeding
leaves it alone. So is any mention below line 1. Your rendered `AGENTS.md` and `CLAUDE.md`
carry no marker at all, so once yours exist they are never re-rendered.

If you *do* want a marked file re-rendered — or want to keep one forever — line 1 is the
whole control: delete it to claim the file, restore it to hand the file back.

(The older "only if it doesn't already exist" rule couldn't work: the kit *ships* those
files, so a copy-in always landed them first and the seed step never fired.)

Then open `config/dev-model.yaml` and fill in anything you skipped — especially
the `tracker` and `models` blocks. That one file is where every skill and script
reads its project-specific values, so there's nothing to hardcode elsewhere.

### Values you don't want in git

`notify.user_key` is an identity — the operator id an approval DM targets — so it
goes in `config/dev-model.local.yaml`, gitignored and merged over the tracked file:

```yaml
# config/dev-model.local.yaml
notify:
  user_key: "U0XXXXXXXXX"
```

It is the only key you may set there; anything else is an error naming what it
refused. `./init.sh` writes the *tracked* file, so a locally-set key keeps winning
after a re-run — leave the tracked value blank rather than duplicating it.

## 2 · Your first briefing — `session-start`

Start your agent and run `session-start`. It reads your handoff, the friction
log, your tracker, open PRs, and CI, then proposes what to do next — grouped by
urgency, each candidate tagged `[size · model · mode]`, ending with one pick:

```text
🧭 Session Start — Mon 2026-01-05

Where things stand
  • main (clean) · 0 open PRs · CI green
  • Last session: scaffolded the auth module

What to do next
🟡 Soon
  • Wire the password-reset endpoint    [M · default · inline]   handoff
🟢 Whenever
  • Backfill tests for the token store  [S · cheap · delegate]   friction-log

👉 My pick: wire the password-reset endpoint — it's the active sprint's next step.
```

The tags are the plan: **size** (S/M/L), which **model tier** the step warrants
(cheap / default / top — match the tier to the difficulty, not the session), and
**mode** — `inline` (work it here) or `delegate` (hand a self-contained task to a
cheaper agent and review the result).

## 3 · Do the work

Two modes, by the shape of the task:

- **Inline (cockpit)** — anything needing judgment or back-and-forth. You and the
  agent work in the main session.
- **Isolated lanes** (`parallel`) — self-contained, *disjoint* tasks run
  concurrently, each in its own git worktree with a sandboxed `state/` directory,
  so parallel agents can't clobber each other's scratch state or the shared plan.
  Map each lane's file footprint first — the sandbox prevents *state* collisions,
  not *source* merge conflicts.

Reserve the top model tier for the one decision that's expensive to get wrong;
let a cheaper tier do the mechanical building.

## 4 · Open a PR and watch it — `pr-watch`

Every change goes through a branch and a PR — and opening the PR is *not* the end
of the task:

```text
/pr-watch 42          # Claude; `$pr-watch 42` in Codex
```

(That's a skill invocation in your agent session, not a shell command — the engine
underneath is `uv run scripts/pr_watch.py 42`.) It polls CI and review comments and
doesn't stop until the PR is **green and clean**:
every check passing, and every review finding either fixed or replied-to with a
reason. A review bot being down isn't a waiver — run an independent review pass
instead.

For a **risky** change — a send-gate, a destructive migration, a recovery/kill
path — the shared safety doctrine (`docs/agentic-dev-kit/safety-critical-changes.md`)
raises the bar: prefer a deterministic gate over a fuzzy matcher, use more than
one review lens, and require an operator sign-off before merge. Those never
self-merge.

## 5 · Close the loop — `wrap-up`

At the end of the session, `wrap-up` updates `docs/handoff.md` with what shipped
and what's next…

```markdown
## Latest session — 2026-01-05

**Theme —** Wired the password-reset endpoint (#42, merged).

- Endpoint + token-expiry check shipped; rate-limit deferred.

▶ Next: add the reset-email template and the rate-limit guard.
```

…and captures any friction you hit into `docs/friction-log.md`, while it's fresh:

```markdown
## 2026-01-05 — inbox

- **`init.sh` didn't detect an existing tracker config (severity: L).** Had to set
  `tracker.linear.project_id` by hand. Fix: probe for a known config file first.
```

Because the next `session-start` reads that handoff, the thread is never lost —
and the friction entry is now queued for the flywheel.

## 6 · Turn the flywheel

On a cadence (weekly works well):

- **`/triage-friction-log`** reads the new inbox entries and routes each one: a
  single incident becomes a tracker ticket, then the entry is swept to the archive.
- **`/post-merge-systemize`** scans recently merged PRs for a pattern that shows up
  in **two or more** of them — and only *then* promotes it into a standing rule.

Single incidents route **down** (to the tracker); repeated patterns route **up**
(to a rule). That asymmetry is deliberate — it's what keeps your rule set small
and your friction log honest instead of ratcheting every week.

> **Note:** these two skills ship as *doctrine* — the prose and routing rules are
> here, but their deterministic engines — a tracker client, a notify channel, a
> merged-PR fetcher, a heartbeat, and `triage-friction-log`'s own parse/finalize
> scripts — are project-specific and left for you to wire
> ([#6](https://github.com/topij/agentic-dev-kit/issues/6),
> [#7](https://github.com/topij/agentic-dev-kit/issues/7)). The four core skills
> (`session-start`, `wrap-up`, `parallel`, `pr-watch`) run out of the box.

## That's the loop

```text
session-start → work (inline or parallel) → pr-watch → wrap-up
                                                               │
                        friction-log ──weekly──► triage + systemize
                                                               │
                                       tickets + rules ──► next session-start
```

Each session leaves the repo more legible than it found it: the handoff carries
the thread forward, the flywheel turns rough edges into tickets and repeated pain
into rules, and the next briefing starts from all of it.
