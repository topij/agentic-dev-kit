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

## 1 · Adopt the kit

Click **Use this template** on GitHub and clone the result, or copy the kit's
contents into an existing repo's root:

```sh
cp -r /path/to/agentic-dev-kit/. .
./init.sh
```

`init.sh` prompts you for a handful of values — project name, agent runtime, tracker, the
protected branch, your review bot — and stamps them into `config/dev-model.yaml`.
It also seeds `docs/handoff.md` and `docs/friction-log.md` (only if they don't
already exist) and adds the state sandbox to `.gitignore`.

Then open `config/dev-model.yaml` and fill in anything you skipped — especially
the `tracker` and `models` blocks. That one file is where every skill and script
reads its project-specific values, so there's nothing to hardcode elsewhere.

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

```sh
pr-watch 42
```

polls CI and review comments and doesn't stop until the PR is **green and clean**:
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
  `tracker.project_id` by hand. Fix: probe for a known config file first.
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
> here, but their deterministic engines (a tracker client, a merged-PR fetcher) are
> project-specific and left for you to wire. The four core skills
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
