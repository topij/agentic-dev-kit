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
sibling `dev-model-sessions/` dir by default (override with `DEVKIT_SESSIONS_DIR`);
your CI/cron runner sets neither env var, so it's unaffected.

**A lane inherits the cockpit's MCP access.** `dev_session.sh new` copies a repo-root
`.mcp.json` into each lane worktree, so every lane can reach the same MCP servers the
cockpit can. If that file holds *literal* credentials rather than `${ENV_VAR}`
references, each lane worktree then holds a copy of them — which is why `init.sh` adds
`.mcp.json` to `.gitignore` when it detects that shape. Prefer `${ENV_VAR}` references
so the file can stay tracked and the lane copies carry no secret.

## Lane authority and resume matrix

The engine artifacts below are one identity chain. Runtime adapters translate how a
command is invoked; they do not replace, relax, or reconstruct this chain.

| Surface | Authoritative inputs | Durable evidence | Failure / resume result |
| --- | --- | --- | --- |
| `new` | configured protected branch and lane prefix; requested branch, base, and merge class | session `branch`, `base`, and `merge_class`; worktree and sandbox | creation failure is not a lane; retry only after accounting for any branch or worktree the failed Git operation left behind |
| `new --headless` | the same identity plus resolved absolute worktree, sandbox, and repository roots; a relative sessions container is anchored to the invocation directory before any write | marker, descriptor, and activation file agree on the resolved roots; descriptor `env` carries the complete lane-root override | an env-incapable launcher cannot resume this as an unattended state-writing lane; use an env-capable launcher or attended activation |
| scope `pr-watch` | one intact session; exact checkout repository; same-repository open PR whose base, head branch, owner, and fork flag match the persisted lane | acknowledgements and review receipt in that session's state root | missing, ambiguous, foreign, or malformed identity refuses before the review engine runs |
| `merge` | persisted `self` class plus the scope-watch identity chain; act-time report for the same PR, base, and head | forge merge pinned to the validated head | any identity movement or failed/ambiguous forge result refuses; re-poll and resume from the exact current head |
| reconciliation | exact checkout repository; authoritative PR list; persisted base/class when a session survives; stable snapshots of every surviving local ref, remote-tracking ref, and live origin branch | `merged`, `held`, `open`, or `parked` row plus the batch exit contract | repository/read/shape failure emits no board and stops; an observed newer or moving branch tip keeps the lane resumable |
| `rm` | persisted branch and base, never the worktree's current branch | merged PR head or ancestor relation before branch deletion | dirty or undeterminable worktree refuses without `--force`; the removal command repeats that guard at act time; unlanded or identity-mismatched branch is kept for recovery |

### Semantic mutation matrix

These are the hostile changes the kit verification surfaces must reject. Engine
branches need behavioral mutations; executed launcher instructions without a shipped
launcher need semantic assertions until an integration surface exists. Add that live
launcher mutation with the environment-capable launcher rather than simulating one here.

| Mutation | Required observable result |
| --- | --- |
| inherit a cockpit `DEVKIT_STATE_ROOT` instead of applying descriptor `env` | descriptor emission replaces the inherited root, and the shared launcher contract rejects `setdefault`; live child-process coverage remains part of the environment-capable launcher slice |
| drop or alter persisted branch, base, or merge class | merge refuses; reconciliation cannot widen the lane to `held` |
| inherit ambient `GH_REPO`, fail a forge read, or return malformed JSON | the engine stops before rendering or authorizing an empty/clean result |
| return a fork, foreign owner, wrong base, or wrong head branch under the requested head name | row is not eligible to identify or terminalize the lane |
| move the PR head between identity read and act-time review | merge refuses before the forge write and asks for a retry |
| return a held probe for another PR, base, or head, or with blockers / non-convergence | lane remains `open` |
| keep a local, cached remote-tracking, or live origin branch tip newer than the selected merged PR, or move a ref in either direction during its snapshot reads | lane remains `open`; the older PR cannot claim the observed work shipped |
| tear down the session before an operator-held decision | the open PR remains `open`; absent class/state evidence is never reconstructed |
| create worktree content after `rm`'s status probe, or remove a dirty/unlanded lane | the non-force Git removal refuses at act time, the session survives, and unlanded branch work remains recoverable |

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

   **That call needs a row limit and field selection**, on the terms
   [`session-start`'s tracker gather](session-start.md) sets out — they are separate
   controls, and the row count is suspect against both your requested limit and the
   backend's own maximum. Do not restate the rules here; follow them there. What is
   specific to *this* gather is the consequence: a truncated briefing under-reports
   and a human reads a short list, but a truncated batch plan silently narrows the
   **input to a set of isolated lanes** — the tickets past the cut are not merely
   unmentioned, they are not worked, and the batch reports success over the subset it
   happened to see. Nothing downstream recovers them: clustering, the stale-premise
   pre-flight and the disjointness test all reason over the candidates they were
   handed, so a short list looks exactly like a small backlog.

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

1. **Launch each + relay a kickoff.** Run `<engine-dir>/dev_session.sh new <scope>
   --merge-class <self|operator>` per chosen ticket (see below) and relay each copy-paste line **with a kickoff prompt**
   the operator pastes as the session's first message:

   **Ground each lane brief in the ticket body, not in a summary of it.** Before drafting
   a lane's kickoff, read the ticket itself from your tracker. A brief written from
   `<handoff>` or a plan summary is not acceptable while the ticket is reachable: a
   summary is written to preserve what a ticket is *about*, so anything enumerated in the
   body — an acceptance list, a second deliverable — is exactly what it is free to drop,
   and the brief that results reads complete. The evidence behind this rule is a
   single reported lane whose two named deliverables lived only in the ticket body
   and were retrofitted mid-review — one occurrence, not a survey. Treat the
   mechanism as the general claim and that as its single instance.

   If the tracker read fails (missing key, backend down), the hazard is the **silent
   fallback**, not the failure — so do not quietly write the brief from the summary
   anyway. Say so *in the brief* and mark it summary-sourced, which is what makes the gap
   actionable by whoever reads it. Then reconcile it against the ticket as soon as the
   tracker is reachable; if your forge and tracker post a linkback on the lane's PR, that
   comment is an earlier and cheaper place to catch the difference.

   > Obtain the lane contract with `<engine-dir>/dev_session.sh print-contract` and
   > follow it for this session — don't infer it from this kickoff, which is
   > task-specific, not the contract itself. Read tracker ticket `<ID>` (+ any recipe
   > in `<handoff>`). Pre-flight its premise against the live code before coding.
   > Branch `<branch>` is ready. **Suggested effort: `<tier>`**
   > (`<one-line risk reason>`) — set your session's model (and reasoning effort, if
   > your client exposes that control) accordingly before starting. Heads-up: a
   > parallel session owns `<other-area>` — if you need to touch `<shared-file>`,
   > flag it before committing.

   Interactive `new` prints the configured agent CLI command for the **operator's own
   shell**, so it can only *suggest* the tier — the operator applies it (model and
   reasoning effort, if exposed) when starting the session. An **unattended/headless**
   launcher may set the tier when its runtime exposes that control — see
   [Unattended / headless launch](parallel-headless.md#unattended--headless-launch--new---headless).

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
| **Mechanical** / **Standard**  | **self-merge** *(autonomous/headless batches only)* | the **cockpit**, without operator sign-off, once green-and-clean with one independent review pass — via `dev_session.sh merge`. "Self" means the autonomous process may close it out itself; it never means the lane merges its own PR. |
| **High-stakes**                | **operator-merge**                                  | always the operator, explicitly — never closed out autonomously, even when green |

The class is persisted in the session metadata and headless JSON descriptor;
missing/unknown metadata defaults to **operator**. Operator-merge is the floor for anything in your project's high-risk classes:
data-shape / fetcher / config-semantics changes, shared primitives, a **guard / gate /
verifier / send-path / kill-path** (see
   `docs/agentic-dev-kit/safety-critical-changes.md`), security, PII,
or anything touching production cron/CI or shared `state/`. Normal **interactive**
sessions leave *all* merges to the operator regardless of class — self-merge is an
autonomous-session behavior (see the configured autonomous-session playbook at
`paths.playbook`).
When unsure, classify **operator-merge**.

For an autonomous self-merge, run `<engine-dir>/dev_session.sh merge <scope>`.
That deterministic wrapper re-polls `pr-watch` at act time, requires current-head
independent-review evidence, validates the exact repository/branch/base, and pins the
merge to the reviewed head commit. It refuses any lane whose persisted class is not
`self`. Operator-class lanes intentionally cannot use the wrapper; the operator lands
those directly after the required review and sign-off.

**How the tier reaches the lane.** It depends on the launch mechanism:

- **Headless lanes — fan out through a multi-agent workflow when it exposes a real
  effort dial.** Such a launcher passes each lane its
  tier directly — one sub-agent per lane, each given its own `effort`/`model` — so
  **both** halves of the tier (reasoning effort *and* model) actually take effect.
  Use this path when the runtime supports it and lanes are tiered differently. Recipe + caveats in [Unattended / headless
  launch](parallel-headless.md#unattended--headless-launch--new---headless).
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
merged, consciously parked, or **held** for an operator merge decision — run the joint
wrap-up **from this cockpit session**:

1. **Reconcile every launched scope to a terminal state first — before reading any
   narrative or writing any block.** An aggregate "all merged" is *not* evidence a
   scope shipped: a silently-dead session (never started, 0 commits, no PR, branch
   still at the base tip) can get closed as done if nothing checked per-branch. Run
   the reconciler over the batch's launched scopes:

   ```bash
   <engine-dir>/reconcile_sessions.sh <scope-1> <scope-2> <scope-3>
   ```

   For each `<prefix>/<scope>` — `vcs.dev_branch_prefix`, which the reconciler reads
   itself and `--prefix` overrides — it lists that branch's PRs (`gh pr list --head
   <prefix>/<scope> --state all`) and classifies the newest one itself, rather than
   asking the forge only for merged ones: a stale merged PR would otherwise mask the
   in-flight PR that is the lane's actual state. It resolves
   **merged**; **held** (an operator-class lane whose open PR is already merge-ready —
   green, review-clean, receipt bound to head — so only your merge decision is
   missing); **parked** with the reason (`EMPTY — 0 commits, never started`, `PR closed
   unmerged`, `N commit(s), no PR opened`); or **open** (still in flight). It then
   prints the `launched N, merged M, parked K` tally, which grows a `held H` term when
   any scope is held — exit 3 if any scope is open or parked, **4** if every scope is
   merged or held with at least one held, 0 only when all merged, and **64** when a
   required forge or identity read fails. Exit 64 invalidates the snapshot: the engine
   emits no lane board, and callers must stop rather than infer an empty or partial
   result. **Do not write the
   wrap-up block until every launched scope is merged, consciously parked, or held.** A
   scope that reconciles to **open** means the batch isn't closeable — finish or park it
   first. A scope that reconciles to **parked** gets named as parked in the block, never
   folded into "all shipped"; a scope that reconciles to **held** gets named as awaiting
   your merge, with its PR number — it has NOT shipped either. (Pass the scopes
   explicitly — `rm` removes session dirs, so a scope already torn down won't
   auto-discover; the cockpit knows the launched set. `held` needs the session dir: a
   torn-down lane has no persisted merge class or state sandbox left to read, and falls
   back to `open`.)

   The reconciler is **mechanism-agnostic** — it keys on branch / PR head ref, so it
   also covers batches *not* launched via `parallel` (a background sub-agent fan-out,
   headless lanes). For those, pass branches directly or a glob instead of scopes:

   ```bash
   <engine-dir>/reconcile_sessions.sh --match 'feat/login-*'   # every local+remote branch matching the glob
   ```

   With no args it discovers in-flight lanes from **both** session dirs and live `git
   worktree`s (deduped by branch), so a background-sub-agent worktree gets the same
   `launched/merged/parked` net that catches a dead session.

   Reconciliation is a quiescent snapshot, not a lock against another pusher. It reads
   every surviving local ref, cached remote-tracking ref, and live origin branch
   repeatedly and keeps a lane open when a ref differs from the PR head or moves during
   those reads. A failed live-origin read invalidates the snapshot like a failed forge
   read. Do not mutate the launched refs while the snapshot runs; work that begins after
   its final ref read belongs to the next reconciliation.

1. Read each **merged** and **held** PR's narrative: `gh pr view <n> --json title,body`
   per merged or held batch PR (parked scopes have no landed narrative to read; a held
   one has a finished PR body and is exactly what you need in order to rule on it).

1. Write **one** "Latest session" block for the whole batch via `wrap-up` — open
   with the tally line, then PRs landed, collisions avoided, each parked scope with
   its reason, and each held scope with its PR number and what it is waiting on. Not
   one block per session.

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
<engine-dir>/dev_session.sh new <scope> --merge-class <self|operator>
```

substituting a lowercase slug for `<scope>` (e.g. `feat-graduation-flow`). Pass
`--runtime <name>` to select a configured launcher or `--launcher <command>` to
override it for this lane. The script
prints a copy-paste line — `cd <worktree> && export DEVKIT_STATE_ROOT=… && export
DEVKIT_ROOT=… && <your agent CLI>`. **Relay that line to the operator** and tell them
to run it in a new terminal; don't try to start the session yourself. Options:
`--base <branch>` (default `vcs.protected_branch`), `--prefix <p>` (default
`vcs.dev_branch_prefix` — parallel-session
branches get their own namespace to avoid colliding with hand-named feature branches),
`--branch <full>` to override the whole name. Omitting `--merge-class` fails safe to
`operator`.

**Git hooks need no per-lane setup.** `git worktree` shares one hooks directory across
the primary checkout and every lane — `git rev-parse --git-common-dir` from inside a lane
resolves back to the primary checkout's `.git` — so `init.sh` only needs to run **once**,
in the primary checkout, and every lane created afterwards already has the hooks. There
is nothing to install per-lane. This matters here because the kit ships `pre-push` and
`dev_session.sh` builds every lane as a worktree, so a lane is covered by the primary
checkout's install or by nothing.

### Unattended / headless launch

For an **unattended** batch — a background sub-agent fan-out, a cloud session, or any
launcher driving a lane with no human at a terminal — `new --headless`, its JSON
descriptor, the lane-contract preamble every headless launch must inject verbatim, and
the workflow-fan-out recipe now live in their own file:
[`parallel-headless.md`](parallel-headless.md). Load it only when you're actually
launching unattended lanes — the board, `plan`, and interactive `new` above never need
it.

## Finishing a session

From the cockpit, drive a lane's review loop through the scope-aware wrapper so its
seen-set and receipt land in the same sandbox the merge gate reads:

```bash
<engine-dir>/dev_session.sh pr-watch <scope> --json
<engine-dir>/dev_session.sh pr-watch <scope> --mark-seen
<engine-dir>/dev_session.sh pr-watch <scope> --record-review <source> --head <polled-sha>
```

The receipt command uses the `head` from the exact poll whose diff was independently
reviewed and refuses if a push landed before recording. For a `self` lane, once this
scope-aware `pr-watch` has converged, merge through the deterministic class gate:

```bash
<engine-dir>/dev_session.sh merge <scope>
```

For an `operator` lane, the wrapper refuses; the operator performs the reviewed,
signed-off merge directly. After its PR has merged:

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
