# Parallel sessions — a step-by-step how-to

This is the task-oriented companion to [`parallel-dev.md`](parallel-dev.md). That
page explains the **model** — cockpit + isolated lanes, disjoint file footprints, why
it's safe. This one is the **recipe book**: for each thing you actually want to do,
the exact commands and *what happens when you run them*.

Examples use the template default `paths.engines: scripts`. If you adopted the kit
under `scripts/devkit`, substitute that configured directory. Invoke the shared
workflow as `/parallel` in Claude Code or `$parallel` in Codex.

If you read only one section, read the next one — it's the point almost everyone
trips on the first time.

## The mental model — three separate things

Starting a parallel session involves three things that are easy to conflate:

1. **This session** — the agent session you're already in. When it runs a `parallel`
   verb it acts as a *launcher / coordinator*. It **does not** turn into the new
   session, and it **does not** touch your current branch, checkout, or scratch state.
2. **The artifacts on disk** — a git **worktree**, a **branch**, and a **state
   sandbox** that `dev_session.sh new` creates. Inert until someone opens them.
3. **The new session** — a *separate* process for the configured agent runtime that you start
   in a **new terminal**. This is the one that actually does work in the new worktree.

The single most common surprise:

> **An in-agent workflow cannot open a new interactive terminal for you.**

A `parallel` skill runs *inside* your current agent process — it can't `cd` your
terminal into a new directory or spawn a fresh REPL there. So for an interactive lane,
`new` does all the setup and then hands you a **copy-paste line**; *you* paste it into
a new terminal to actually start the session. (Headless lanes are the exception — see
[Use case 4](#use-case-4--launch-an-unattended-headless-lane) — because there is no
human terminal to hand the line to.)

So "what is `parallel new` for, if I still have to open the terminal myself?" — it
does everything *except* the one step that fundamentally needs your shell: it creates
the worktree, branch, and sandbox correctly, and emits the exact line to launch into
them. The manual paste is a two-second hand-off, not the work.

Keep that three-way split in mind and every verb below makes sense.

## What each invocation does, at a glance

| You run | What happens | Touches your current branch? | Read-only? |
|---|---|---|---|
| `parallel` &nbsp;or&nbsp; `… list` | Prints the board of active lanes | No | Yes |
| `parallel list --watch` | Same board, auto-refreshing | No | Yes |
| `parallel plan` | Proposes a disjoint batch to launch | No | Yes (until you confirm) |
| `dev_session.sh new <scope>` | Creates worktree + branch + sandbox, prints a launch line | No | No — writes to disk, but **not** to your checkout |
| *(you paste the launch line)* | Starts the new session in a **new terminal** | No | — |

Even `new` doesn't touch *your* working tree: the worktree it creates is a separate
directory under a sibling `<project>-sessions/` folder (override with
`DEVKIT_SESSIONS_DIR`).

---

## Use case 1 — See what's already running

You just want to know what lanes exist and where they stand. This is the safe,
read-only default.

```bash
scripts/dev_session.sh list          # or just run parallel with no argument
```

You get one row per lane: `SCOPE · BRANCH · PR · CI (✓/✗/…) · DIRTY (uncommitted
count) · SANDBOX path`. Nothing is created or changed. If there are no lanes, the table
is empty.

**Follow it live** while a batch is in flight:

```bash
scripts/dev_session.sh list --watch        # re-render every 30s
scripts/dev_session.sh list --watch 10     # …every 10s
```

The watch board marks every row that changed since the last frame with a leading `*`
(CI flipped, a commit landed, the dirty count moved, a PR went draft→ready or merged),
which is also how you spot a **silently-dead lane** that stops moving. `Ctrl-C` to
stop.

---

## Use case 2 — Start one independent session, decoupled from your current branch

This is the "I want a fresh session that isn't tied to what I'm working on right now"
case. One command sets it up:

```bash
scripts/dev_session.sh new <scope>
```

Substitute a lowercase slug for `<scope>` (e.g. `add-rate-limit`, `fix-cli-help`).
`<scope>` is a placeholder — running it literally would create a branch named
`dev/<scope>`, which you don't want.

What this does:

1. Creates a git **worktree** in the sibling `<project>-sessions/` directory (a linked
   worktree sharing this repo's objects — not a full clone).
2. Creates a fresh branch **`dev/<scope>`**, branched off **`origin/main`** by default
   — **not** off your current branch. That's what makes the new session independent:
   it starts from a clean base, so it can't inherit or disturb your in-progress work.
3. Sets up an isolated state sandbox (`DEVKIT_STATE_ROOT`) so the new session's
   scratch-state writes never collide with yours.
4. Prints a **copy-paste line** and stops:

   ```text
   cd <worktree> && export DEVKIT_STATE_ROOT=<sandbox> && export DEVKIT_ROOT=<repo> && <configured-launcher>
   ```

**Then you** open a new terminal and paste that line. That — not the workflow —
is what starts the new agent process. Your current session keeps running, unchanged, on its
own branch.

Useful options:

- `--base <branch>` — branch off something other than `main`. Use this if you
  *deliberately* want the new session to build on another branch (including your
  current one).
- `--prefix <p>` — branch namespace (default `dev`, giving `dev/<scope>`).
- `--branch <full>` — override the whole branch name.
- `--runtime <name>` — select a key from `runtime.launchers` for this lane.
- `--launcher <command>` — override the configured command for this lane; use
  `--launcher none` to print activation-only guidance.

> **Do I even need `new` for a throwaway?** If you only want to read or experiment with
> **no** branch and **no** state isolation, a plain `git worktree add ../scratch main`
> works. But the moment the session runs project scripts that write to `state/cache/`,
> use `new` so the two sessions don't clobber each other's scratch state.

---

## Use case 3 — Plan and launch a *batch* of parallel lanes

When you want several lanes at once, don't spin them up one ticket at a time — compose
the batch so no two lanes edit the same source file (the sandbox prevents *state*
collisions, not *source* merge conflicts). Start from the planner:

```text
parallel plan            # or: parallel plan <focus-area-or-ticket-list>
```

It gathers candidate work, **clusters it by file footprint**, drops stale-premise
candidates, and proposes a disjoint batch — at most one lane per cluster — each tagged
with an **effort tier** and a **merge class** (self-merge vs operator-merge). You
confirm the set, then it launches a lane per pick with `dev_session.sh new` and relays
each launch line.

From there, **this session becomes the cockpit**: it owns the shared narrative files
and the merges, watches `list --watch`, and does the reconcile + wrap-up at the end.
The full planning method, the lane contract, and a worked four-ticket example live in
[`parallel-dev.md`](parallel-dev.md#the-workflow) — this how-to intentionally doesn't
duplicate it.

---

## Use case 4 — Launch an unattended (headless) lane

A headless lane has **no human terminal** to hand a launch line to, so `new` behaves
differently:

```bash
scripts/dev_session.sh new <scope> --headless
```

Instead of printing a copy-paste line, `--headless` writes a sticky
`<worktree>/.devkit_state_root` marker file so the agent's tool calls resolve the
sandbox from disk (they don't inherit a shell), and emits a machine-readable descriptor
whose `prompt_preamble` carries the **lane contract** — draft PR, actively poll your
own CI to green, never touch the narrative files, check `git branch --show-current`
before every commit. See the exact contract text with:

```bash
scripts/dev_session.sh print-contract
```

This is the path a `Workflow`- or `Agent`-driven fan-out uses to start lanes itself, no
operator paste involved. Interactive `new` and your CI/cron runner never set the marker,
so their behavior is unchanged.

---

## Use case 5 — Wind a session down

When a lane's PR is merged (or you're abandoning it), reconcile and tear down.

**Find a lane's sandbox path** (e.g. to inspect its scratch state):

```bash
scripts/dev_session.sh path <scope>
```

**Reconcile the whole batch to a terminal state** before you write anything to the
shared handoff — an aggregate "everything's done" is not evidence a specific lane
shipped:

```bash
scripts/reconcile_sessions.sh <scope-1> <scope-2> …   # merged / parked / open, per lane
```

**Remove the worktree** once you're done with it:

```bash
scripts/dev_session.sh rm <scope>                 # keeps the branch if it's unmerged
scripts/dev_session.sh rm <scope> --keep-branch   # always keep the branch
scripts/dev_session.sh rm <scope> --force          # skip the safety checks
```

`rm` tears down the *worktree*; it does not delete an unmerged branch unless you tell
it to. Your cockpit session and current branch are untouched throughout.

---

## FAQ

**Does any of this affect my current branch or checkout?**
No. Every verb either reads state (`list`, `plan`, `path`) or creates a *separate*
worktree (`new`). Your current session stays on its own branch the whole time.

**Does the new session branch off my current branch?**
No — off `origin/main` by default, so it starts clean. Pass `--base <branch>` if you
specifically want it based on something else (including your current branch).

**Why can't `parallel new` just open the new session for me?**
Because an in-agent workflow runs inside your current agent process. It can't move your
terminal into a new directory or start a fresh agent process there — that needs your shell.
So it does everything up to that point and hands you the launch line. Headless lanes
skip the hand-off because there's no terminal involved.

**Is running `parallel` (no argument) ever destructive?**
No. With no argument it just prints the board and stops. It's the `git status` of your
lane fleet.

## See also

- [`parallel-dev.md`](parallel-dev.md) — the concept: cockpit + isolated lanes,
  disjoint footprints, the batch workflow, the worked example.
- [`agentic-dev-kit/workflows/parallel.md`](agentic-dev-kit/workflows/parallel.md) — the shared workflow.
- [`PRINCIPLES.md`](../PRINCIPLES.md) #3 (cockpit + isolated lanes), #7 (effort
  tiering).
