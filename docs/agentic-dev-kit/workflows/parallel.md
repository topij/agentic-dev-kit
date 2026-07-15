# Parallel development

Manage isolated **parallel dev sessions** — each one its own git worktree on a fresh
branch plus its own `DEVKIT_STATE_ROOT` sandbox, so several agent/dev sessions run at
once without clobbering each other's checkout or `state/cache/`. Thin in-session
front-end over the configured lane engine (the activation of the state-sandbox
primitive — see Principle #3 in `PRINCIPLES.md`).

Read `config/dev-model.yaml` first. Resolve `<engine-dir>` from `paths.engines`,
`<handoff>` from `paths.handoff`, and `<friction-log>` from `paths.friction_log`.
Treat `cheap`, `default`, and `expensive` as neutral capability tiers and translate
them through `models.runtime_mappings` only when the current runtime supports that
control. A workflow invocation means `/name` in Claude or `$name` in Codex.

Engine: `<engine-dir>/dev_session.sh`. Sessions live in a
sibling `<project>-sessions/` dir by default (override with `DEVKIT_SESSIONS_DIR`);
your CI/cron runner sets neither env var, so it's unaffected.

## Default action — show the board

With no argument (or `parallel list`), run and render the table of active sessions:

```bash
<engine-dir>/dev_session.sh list
```

Columns: `SCOPE · BRANCH · PR · CI (✓/✗/…) · DIRTY (uncommitted count) · SANDBOX
path`. This is the orientation surface when you're juggling several sessions — report
it as-is, then stop. Read-only.

### Live board — `parallel list --watch [interval]`

`list` is a one-shot snapshot. To *follow* in-flight lanes — CI flips, commits
landing, the DIRTY count moving, a PR going draft→ready or merging, or a silently-dead
lane that never moves — run the polling board instead:

```bash
<engine-dir>/dev_session.sh list --watch        # re-render every 30s
<engine-dir>/dev_session.sh list --watch 10     # …or every 10s
```

It re-renders on the interval and **marks with a leading `*`** (bold on a TTY) every
row whose state changed since the previous render — the change set is CI ✓/✗/…, a new
commit (HEAD moved), a DIRTY-count change, or a PR-state change (draft↔ready, review
decision). The first frame is the baseline (nothing marked); Ctrl-C stops it. On an
interactive terminal an unbounded watch repaints **in place** on the alternate screen
buffer (like `top`) — each frame replaces the last rather than scrolling a fresh copy
into your terminal history, and your pre-watch screen is restored when you Ctrl-C out
(a board taller than the window is clipped while watching, as with any full-screen
tool — use a taller window). A bounded `--max-iters` run instead leaves its final
frame on screen. The per-row SANDBOX cell is the compact `<scope>/state` tail (the
shared sandbox root is named once in the banner) so rows don't wrap on a long
absolute path — **this compaction applies to piped output too**; for the full
absolute sandbox path use bare `list`. Piped/redirected, the board is plain
escape-free text. Each `gh` lookup keeps the same short timeout as bare `list`, so a
slow network caps per-call and never hangs the loop. Use it as the cockpit's ambient
board while a batch is running rather than re-typing `list`.

## Planning a batch — `parallel plan [focus]`

When the operator wants to **start several sessions at once** (or asks "what could we
work on in parallel?"), don't jump to `new` ticket-by-ticket. The suitability test for
parallel work is **disjoint file footprints**: two sessions are safe together only
when no source file is edited by both. The sandbox makes concurrent `state/cache/`
*writes* safe — it does **nothing** for two branches editing the same source file
(that's a merge conflict + diluted review at PR time). So compose the batch
deliberately:

1. **Orient.** `<engine-dir>/dev_session.sh list` + `git worktree list` — active sessions
   are file territory already claimed; exclude their footprints from the new batch.

1. **Gather candidates.** Pull open tickets from your tracker (project
   `tracker.project_name`, states In Progress + Todo) and the `▶ Next` deferred items
   in `<handoff>`. If a `<focus>` argument was given (a
   theme, an area, or an explicit ticket list), scope to it.

1. **Cluster by file footprint.** Group candidates by the files/dirs each one
   touches — read the ticket and grep the code when unsure; don't infer the footprint
   from the title. Present the clusters as a table. Within a cluster, pick **at most
   one**; the rest go sequential.

1. **Stale-premise pre-flight.** Flag any candidate whose fix may already be shipped
   (checklist items matching recently-merged PRs; a "Done" tracker state that might be
   a bot-driven auto-complete rather than actual code). Verify against the live code
   **before** recommending it — premise-check-before-build is the house style.

1. **Scope outward-safe.** A session that would push to an external system, send a
   notification, or post to a customer-facing channel gets scoped to its **in-repo /
   authoring half**; the gated outward step stays an operator action after merge.

1. **Assign an effort tier.** The risk read you just did (cluster + stale-premise +
   outward-safe) also sets **how much reasoning each lane gets** — tag each chosen
   lane `low` / `medium` / `high` (→ `max` for the gnarliest) from the [lane-risk →
   effort tier map](#per-lane-effort-tier-risk--reasoning-effort--model) below, so the
   launch step can resource it.

1. **Recommend + confirm.** Propose a disjoint batch (one ticket per cluster) plus the
   residual shared-file watch-outs (e.g. two tickets that *might* both touch the same
   schema file), then let the operator choose the set. Tag each proposed lane with
   **both** its effort tier and its [merge class](#per-lane-merge-class-self-merge-vs-operator-merge)
   (self-merge / operator-merge) up front — deciding the merge boundary at plan time,
   not at merge time, stops a batch stalling on ad-hoc "can I merge this?" calls and
   tells each lane whether it may self-merge or must hand back.

1. **Launch each + relay a kickoff.** Run `<engine-dir>/dev_session.sh new <scope>` per
   chosen ticket (see below) and relay each copy-paste line **with a kickoff prompt**
   the operator pastes as the session's first message:

   > Read tracker ticket `<ID>` (+ any recipe in `<handoff>`). Pre-flight its
   > premise against the live code before coding. Branch `dev/<scope>` is ready.
   > **Suggested effort: `<tier>`** (`<one-line risk reason>`) — set your session's
   > model (and reasoning effort, if your client exposes that control) accordingly
   > before starting. Draft PR on first push → mark ready when done → `pr-watch` to
   > green. Heads-up: a parallel session owns `<other-area>` — if you need to touch
   > `<shared-file>`, flag it before committing. **Do not edit `<handoff>` or
   > `<friction-log>`** — those are cockpit-owned; put your handoff (what
   > shipped, lessons, deferrals) in the **PR body** so the joint wrap-up can
   > aggregate it.

   Interactive `new` prints the configured agent CLI command for the **operator's own
   shell**, so it can only *suggest* the tier — the operator applies it (model and
   reasoning effort, if exposed) when starting the session. An **unattended/headless**
   launcher may set the tier when its runtime exposes that control — see
   [Unattended / headless launch](#unattended--headless-launch--new---headless).

After launch, **this** session is the cockpit: `list` (or `list --watch` for an
auto-refreshing board that flags each CI/commit/PR transition) is the live board, and
you sequence (merge → rebase) any two PRs that end up sharing a file. Two-collision
example worth stating to the operator up front: if two batched tickets both live under
one package but edit different files, they're safe — name the one file (often a
shared schema module) that would force them sequential if both need it.

### Per-lane effort tier (risk → reasoning effort + model)

A mechanical doc lane shouldn't burn max-effort on your most expensive model, and a
shared-primitive lane shouldn't run at low effort. Map each chosen lane to a tier from
its risk:

| Lane risk               | Typical work                                                                                                                                                                                    | Effort                             | Model                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- | -------------------------------------------- |
| **Mechanical**          | doc/comment-only edits, rename, copy tweak, config-value bump, dead-code delete, a `_latest`-rename sweep                                                                                        | `low`                               | inherited (`cheap` is fine)          |
| **Standard** (default)  | a normal feature/bugfix scoped to one package, test additions, a self-contained script                                                                                                          | `medium`                            | inherited (`default`)                |
| **High-stakes**         | schema / data-shape change, a shared primitive (a state-sandbox library, a pipeline-state helper), a guard / gate / verifier, security, anything touching production cron/CI or shared `state/`, the merge-rules / scoring core | `high` (→ `max` for the gnarliest) | `expensive`                          |

When unsure, round **up** — under-resourcing a risky lane costs a bad merge;
over-resourcing a cheap one costs only tokens.

### Per-lane merge class (self-merge vs operator-merge)

The same risk read that sets the effort tier also sets **who lands the PR** —
pre-classify it at plan time so a green lane isn't left waiting on an ad-hoc merge
decision (and so an autonomous batch knows what it may close itself):

| Lane risk                     | Merge class                                         | Who merges                                                                   |
| ------------------------------ | ---------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Mechanical** / **Standard**  | **self-merge** *(autonomous/headless batches only)* | the lane (or cockpit), once green-and-clean with one independent review pass |
| **High-stakes**                | **operator-merge**                                  | always the operator — never self-merged, even when green                     |

Operator-merge is the floor for anything in your project's high-risk classes:
data-shape / fetcher / config-semantics changes, shared primitives, a **guard / gate /
verifier / send-path / kill-path** (see
   `docs/agentic-dev-kit/safety-critical-changes.md`), security, PII,
or anything touching production cron/CI or shared `state/`. Normal **interactive**
sessions leave *all* merges to the operator regardless of class — self-merge is an
autonomous-session behavior (see
   the configured autonomous-session playbook (`paths.playbook`).
When unsure, classify **operator-merge**.

**How the tier reaches the lane.** It depends on the launch mechanism:

- **Headless lanes — fan out through a multi-agent workflow when it exposes a real
  effort dial.** Such a launcher passes each lane its
  tier directly — one sub-agent per lane, each given its own `effort`/`model` — so
  **both** halves of the tier (reasoning effort *and* model) actually take effect.
  Use this path when the runtime supports it and lanes are tiered differently. Recipe + caveats in [Unattended / headless
  launch](#unattended--headless-launch--new---headless).
- **Headless lanes — a single background sub-agent per lane is the *model-only*
  fallback.** If your agent runtime's background-task tool exposes `model` but no
  `effort` parameter, spawning lanes as individual sub-agents sets each lane's *model*
  per the tier while the *effort* reaches it only as a prose hint in the prompt
  ("tier: high, think carefully") — nominal, not a real setting. Fine when there's a
  single lane, when every lane shares a tier, or when you want independently-stoppable
  cockpit-side agent objects; use the workflow-fan-out path when per-lane effort
  differentiation is the point. Either way the tier is **sourced from the plan's risk
  assessment**, one per lane.
- **Interactive `new` lanes**: the kickoff only *suggests* the tier (above); the
  operator sets their own session's effort/model.

**Default-safe.** A lane with no assigned tier inherits the cockpit's current
effort/model — i.e. unspecified ⇒ today's behavior, no regression. The tier is an
*optimization* of a working default, never a prerequisite.

### Joint wrap-up — the cockpit owns the handoff

`<handoff>` and `<friction-log>` are shared *narrative* files: a
per-session edit to either collides at merge **and** pollutes a focused code PR, so
sessions never touch them (the kickoff says so). Each session's handoff rides its
**PR body** — the one channel that's committed, reviewed, and visible across
worktrees (dev-session `state/` sandboxes are isolated by design, so a session's
worktree scratch is invisible to the cockpit). When the batch is closed — every PR
merged or consciously parked — run the joint wrap-up **from this cockpit session**:

1. **Reconcile every launched scope to a terminal state first — before reading any
   narrative or writing any block.** An aggregate "all merged" is *not* evidence a
   scope shipped: a silently-dead session (never started, 0 commits, no PR, branch
   still at the base tip) can get closed as done if nothing checked per-branch. Run
   the reconciler over the batch's launched scopes:

   ```bash
   <engine-dir>/reconcile_sessions.sh <scope-1> <scope-2> <scope-3>
   ```

   For each `dev/<scope>` it resolves a **merged** PR (`gh pr list --head dev/<scope>
   --state merged`) or marks it **parked** with the reason (`EMPTY — 0 commits, never
   started`, `PR closed unmerged`, `N commit(s), no PR opened`) or **open** (still in
   flight), then prints the `launched N, merged M, parked K` tally — exit 3 if any
   scope is open or parked, 0 only when all merged. **Do not write the wrap-up block
   until every launched scope is merged or consciously parked.** A scope that
   reconciles to **open** means the batch isn't closeable — finish or park it first. A
   scope that reconciles to **parked** gets named as parked in the block, never folded
   into "all shipped". (Pass the scopes explicitly — `rm` removes session dirs, so a
   scope already torn down won't auto-discover; the cockpit knows the launched set.)

   The reconciler is **mechanism-agnostic** — it keys on branch / PR head ref, so it
   also covers batches *not* launched via `parallel` (a background sub-agent fan-out,
   headless lanes). For those, pass branches directly or a glob instead of scopes:

   ```bash
   <engine-dir>/reconcile_sessions.sh --match 'feat/login-*'   # every local+remote branch matching the glob
   ```

   With no args it discovers in-flight lanes from **both** session dirs and live `git
   worktree`s (deduped by branch), so a background-sub-agent worktree gets the same
   `launched/merged/parked` net that catches a dead session.

1. Read each **merged** PR's narrative: `gh pr view <n> --json title,body` per merged
   batch PR (parked scopes have no landed narrative to read).

1. Write **one** "Latest session" block for the whole batch via `wrap-up` — open
   with the `launched N, merged M, parked K` line, then PRs landed, collisions
   avoided, and each parked scope with its reason. Not one block per session.

1. Open it as its own `chore: update handoff` PR (this checkout sits on the protected
   branch, so the handoff edit goes through a branch + PR like everything else;
   mirrors the existing `chore: update handoff` cadence).

Overflow that doesn't fit a PR body (richer lessons, friction-log entries) goes to a
uniquely-named `docs/handoff/<scope>.md` fragment that rides the session's **own** PR
— disjoint path, zero collision — and the cockpit folds it into the wrap-up block and
deletes it. Start with PR-body-primary; only reach for fragments when bodies prove too
thin.

## Starting a new session

An interactive session must be launched from the operator's **own shell** (an
in-agent workflow cannot `cd` the operator into a new worktree and open a fresh
terminal there). When asked to prepare one, run:

```bash
<engine-dir>/dev_session.sh new <scope>
```

substituting a lowercase slug for `<scope>` (e.g. `feat-graduation-flow`). Pass
`--runtime <name>` to select a configured launcher or `--launcher <command>` to
override it for this lane. The script
prints a copy-paste line — `cd <worktree> && export DEVKIT_STATE_ROOT=… && export
DEVKIT_ROOT=… && <your agent CLI>`. **Relay that line to the operator** and tell them
to run it in a new terminal; don't try to start the session yourself. Options:
`--base <branch>` (default `main`), `--prefix <p>` (default `dev` — parallel-session
branches get their own namespace to avoid colliding with hand-named feature branches),
`--branch <full>` to override the whole name.

### Unattended / headless launch — `new --headless`

Interactive `new` is operator-launched by design (it prints a copy-paste line and the
rule above says *don't start the session yourself*). That's the wrong shape for an
**unattended** batch — a background sub-agent or a cloud session that should drive a
*sandboxed* lane without a human in the loop. `--headless` is for exactly that:

```bash
<engine-dir>/dev_session.sh new --headless <scope>
```

It creates the worktree + sandbox exactly as `new` does, but instead of the human
block it:

1. **Writes a sticky `<worktree>/.devkit_state_root` marker** holding the absolute
   sandbox path. This is the mechanism that makes a headless lane safe: a background
   sub-agent's shell calls don't share a shell, so an exported `DEVKIT_STATE_ROOT`
   doesn't survive call-to-call. Your state-sandbox resolver reads the marker
   (walking up from cwd) when the env var is unset, so the lane's `state/` writes
   isolate into the sandbox **automatically** — no env gymnastics in the prompt.
   (Precedence: env var → marker → repo-root default. Cron/CI writes no marker, so
   it's unaffected.)
1. **Prints a JSON descriptor to stdout** (diagnostics go to stderr, so stdout is
   clean JSON): `{"scope","branch","worktree","state_root","repo_root","base",
   "prompt_preamble","env","runtime","launcher"}`. `prompt_preamble` is the canonical lane-contract text
   below — the launcher **MUST** prepend it verbatim to the lane's task prompt. `env`
   (currently `{"DEVKIT_REFUSE_UNSANDBOXED_STATE": "1"}`) flips the unsandboxed-write
   guard from *warn* to *refuse*, by default, for every headless lane — so a lane
   whose marker resolution somehow fails (deleted marker, cwd escaped the worktree)
   hard-errors on a `state/` write instead of silently landing in prod. Interactive
   `new` and cron/CI never set either field.

### The lane-contract preamble (inject this verbatim)

Every mechanism that hands a task prompt to a headless lane — a multi-agent
workflow fan-out, a single-background-sub-agent fallback, or any future launcher —
**MUST prepend the same fixed contract text** ahead of the task-specific
instructions. This is the fix for an idle-stall failure mode: a rule that lives only
in a memory or in this doc's prose can't bind a freshly spawned lane, because a fresh
agent has no memory and doesn't read `parallel.md` unless told to. The contract must
be *in the prompt itself*, every time.

Fetch the current text with `<engine-dir>/dev_session.sh print-contract` (plain text, no
JSON) or read it straight off the `prompt_preamble` field of any `new --headless`
descriptor — **do not hand-copy or paraphrase it into this workflow or a launcher**.
Always read it fresh from one of those two engine surfaces so a future edit propagates
without maintaining a second copy.

**Launch contract (cockpit usage).** Every supported launcher drives the same `new
--headless` worktrees. Each launcher **MUST prepend the lane-contract preamble to
every lane prompt**; runtime capability changes how tiers are applied, not whether
the safety contract binds.

**Preferred when available — a workflow launcher with a real effort dial.** Run
`new --headless <scope>` once per chosen scope, collect each one's JSON descriptor
into a list (attaching the per-lane `effort`/`model` tier from the plan's risk read),
then drive the lanes from a *single* fan-out that gives each sub-agent its own
`{effort, model}` — the one path on which the tier's `effort` half actually takes
effect. Pseudocode:

```js
// args.lanes = [{scope, worktree, branch, ticket, effort, model, prompt_preamble}, …]
// — one per `new --headless` descriptor (prompt_preamble copied straight off it).
// effort ∈ low|medium|high|max (omit ⇒ inherit cockpit effort); model ∈ cheap|default|expensive (omit ⇒ inherit).
runInParallel(args.lanes.map(lane => () =>
  spawnAgent(
    `${lane.prompt_preamble}\n\n` +
    `Work in worktree ${lane.worktree} on branch ${lane.branch} (cd there first — its state sandbox is active via the on-disk marker, so your state/ writes isolate automatically). ` +
    `Read tracker ticket ${lane.ticket}, pre-flight its premise against the live code, implement, draft PR on first push, drive it to green-and-clean, then hand off per the contract above.`,
    { label: lane.scope, effort: lane.effort, model: lane.model } // omit effort/model to inherit (default-safe)
  )
))
```

Four things to keep right: **(1)** `lane.prompt_preamble` is prepended verbatim,
ahead of everything else, on every lane — never abbreviated to "follow the usual
contract" (that's exactly the prose-reference that failed to bind a lane before).
**(2)** do **not** open a second worktree on top of `--headless` — it already owns the
worktree+sandbox, so a second one would have no marker and lose isolation. **(3)** A
lane with no assigned tier omits `effort`/`model` and inherits the cockpit's — the
same default-safe fallback as everywhere else. **(4)** Check what compute budget your
fan-out mechanism draws from before running a large batch, and monitor it via
whatever live-progress view your runtime exposes, plus `list --watch` on the lanes'
branches/PRs.

Note on the `env` field: if your fan-out or background-agent tool doesn't expose a
parameter to inject env vars into the spawned lane's process, `DEVKIT_REFUSE_
UNSANDBOXED_STATE` cannot be force-set through that launch path the way
`prompt_preamble` can be force-injected into the prompt text. In the normal case this
is moot: the marker already resolves the sandbox, so the guard never fires. The `env`
field exists for launchers that DO control the spawned process's environment (a
custom subprocess-based batch driver) — read it and export it there. Treat this as a
documented, conservative gap, not a silent one.

**Fallback — a single background sub-agent per lane (model-only).** Parse the
descriptor and spawn a background sub-agent whose prompt is **the `prompt_preamble`
field, prepended verbatim**, followed by the task-specific instructions naming the
`worktree` path — e.g. *"`<prompt_preamble>` Work in worktree `<worktree>` on branch
`<branch>`. The state sandbox is active via its on-disk marker — your `state/` writes
isolate automatically. Read tracker ticket `<ID>`, pre-flight its premise, draft PR on
first push, drive it to green-and-clean, then hand off per the contract above."* Same
no-second-worktree rule and same prepend-verbatim requirement as the workflow path.
This path sets each lane's `model` per the tier but **not its effort** if your
runtime's background-task tool has no effort dial — fine for a single lane, lanes that
all share a tier, or when you want individually-stoppable cockpit-side agent objects.
The how-the-tier-reaches-the-lane mechanics + the default-safe fallback live in
[Per-lane effort tier](#per-lane-effort-tier-risk--reasoning-effort--model).

**When to use which.** Attended work (operator at a terminal) → plain `new`.
Unattended pipeline-touching work (any lane that writes `state/cache/`) → `new
--headless` so the sandbox is active without a surviving shell export. This is the
`parallel` vs bare-background-agent decision rule: *does the lane write `state/`? →
it needs a sandbox → `new --headless`, not a bare background worktree.* This should be
**guarded, not just documented**: your state-sandbox write path should warn when an
unsandboxed lane (no `DEVKIT_STATE_ROOT`, no marker, job-name env unset, in a linked
worktree) writes repo-root `state/` — and `new --headless` sets
`DEVKIT_REFUSE_UNSANDBOXED_STATE=1` by default (the `env` descriptor field + activate
snippet above) to make that a hard error rather than a warning. Cron/CI and normal-
interactive paths are unaffected.

## Finishing a session

After its PR has merged:

```bash
<engine-dir>/dev_session.sh rm <scope>
```

Removes the worktree + sandbox; deletes the branch only if it's merged into the
protected branch (kept with a warning otherwise). Refuses if the worktree has
uncommitted changes unless `--force`. `<engine-dir>/dev_session.sh path <scope>` prints the
worktree path (handy for `cd "$(<engine-dir>/dev_session.sh path <scope>)"`).

## Notes

- **Why the sandbox.** Writes from a session (any skill/script that writes `state/`)
  land in that session's sandbox; shared-cache *reads* take the newer of
  sandbox-vs-main so a session still sees fresh prod caches read-only. This is what
  lets two sessions run data skills concurrently without corrupting `state/cache/`.
  See Principle #3 in `PRINCIPLES.md`.
- **Pairs with** `session-start` (orient within one session) and your project's
  branching convention (draft PR → ready → watch-and-fix). `parallel` is the
  *across-sessions* view; `session-start` is the *within-session* one.
- Read-only by default (`list`; `plan` is read-only until the operator confirms a
  batch). `new`/`rm` mutate worktrees only — never the repo's own tree, never prod
  `state/`.
