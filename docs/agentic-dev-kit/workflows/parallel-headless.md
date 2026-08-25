# Unattended / headless parallel lanes

Companion to [`parallel.md`](parallel.md), split out so an agent only pays for this
content when it's actually launching an **unattended** lane — a background sub-agent
fan-out, a cloud session, or any launcher driving a lane with no human at a terminal.
The board (`list` / `list --watch`), `plan`, interactive `new`, the per-lane
effort-tier and merge-class tables, finishing a session, and the joint wrap-up all stay
in [`parallel.md`](parallel.md); this file is only the headless launch mechanics:
the `--headless` flag, its JSON descriptor, the lane-contract preamble every headless
launch must inject verbatim, and the fan-out recipe.

### Unattended / headless launch — `new --headless`

Interactive `new` is operator-launched by design (it prints a copy-paste line and the
rule above says *don't start the session yourself*). That's the wrong shape for an
**unattended** batch — a background sub-agent or a cloud session that should drive a
*sandboxed* lane without a human in the loop. `--headless` is for exactly that:

```bash
<engine-dir>/dev_session.sh new --headless <scope> --merge-class <self|operator>
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
   "merge_class","prompt_preamble","env","runtime","launcher"}`. `prompt_preamble` is the canonical lane-contract text
   below — the launcher **MUST** prepend it verbatim to the lane's task prompt. `env`
   carries lane-specific `DEVKIT_STATE_ROOT`, `DEVKIT_ROOT`, and
   `DEVKIT_REFUSE_UNSANDBOXED_STATE=1`. The launcher **MUST replace inherited values
   with this map**: the resolver gives an explicit env root precedence over the marker,
   so inheriting the cockpit's root would collapse every child lane into one sandbox.
   The refusal flag flips the unsandboxed-write guard from *warn* to *refuse* — so a lane
   whose marker resolution somehow fails (deleted marker, cwd escaped the worktree)
   hard-errors on a `state/` write instead of silently landing in prod. Interactive
   `new` and cron/CI never set either field.

   Replacement is per descriptor key, not replacement of the entire process
   environment: begin with the launcher's permitted/scrubbed environment, then assign
   every key from `env` unconditionally. Do not use `setdefault`, skip a key because it
   is already present, or rely on the marker to beat an inherited root. Unrelated
   permitted variables remain available; the descriptor map is complete for lane-root
   identity, not a complete process environment.

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
`new --headless <scope> --merge-class <class>` once per chosen scope, collect each one's JSON descriptor
into a list (attaching the per-lane `effort`/`model` tier from the plan's risk read),
then drive the lanes from a *single* fan-out that gives each sub-agent its own
`{effort, model}` — the one path on which the tier's `effort` half actually takes
effect. Pseudocode:

```js
// args.lanes = [{scope, worktree, branch, ticket, effort, model, merge_class, prompt_preamble, env}, …]
// — one per `new --headless` descriptor (prompt_preamble copied straight off it).
// effort ∈ low|medium|high|max (omit ⇒ inherit cockpit effort); model ∈ cheap|default|expensive (omit ⇒ inherit).
runInParallel(args.lanes.map(lane => () =>
  spawnAgent(
    `${lane.prompt_preamble}\n\n` +
    `Work in worktree ${lane.worktree} on branch ${lane.branch} (cd there first — its state sandbox is active via the on-disk marker, so your state/ writes isolate automatically). ` +
    `Read tracker ticket ${lane.ticket}, pre-flight its premise against the live code, implement, draft PR on first push, drive it to green-and-clean, then hand off per the contract above.`,
    { label: lane.scope, effort: lane.effort, model: lane.model, env: lane.env }
  )
))
```

Five things to keep right: **(1)** `lane.prompt_preamble` is prepended verbatim,
ahead of everything else, on every lane — never abbreviated to "follow the usual
contract" (that's exactly the prose-reference that failed to bind a lane before).
**(2)** do **not** open a second worktree on top of `--headless` — it already owns the
worktree+sandbox, so a second one would have no marker and lose isolation. **(3)** A
lane with no assigned tier omits `effort`/`model` and inherits the cockpit's — the
same default-safe fallback as everywhere else. **(4)** replace the spawned process's
environment roots with `lane.env`; do not merge them over inherited cockpit roots.
**(5)** Check what compute budget your
fan-out mechanism draws from before running a large batch, and monitor it via
whatever live-progress view your runtime exposes, plus `list --watch` on the lanes'
branches/PRs.

The `env` field is mandatory for unattended launches. If a fan-out/background-agent
tool cannot replace the spawned process's environment, do not use it for a headless
state-writing lane; use an env-capable subprocess/fresh terminal or keep the work
attended. Prompt injection cannot override an inherited `DEVKIT_STATE_ROOT`.

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
[Per-lane effort tier](parallel.md#per-lane-effort-tier-risk--reasoning-effort--model).

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
