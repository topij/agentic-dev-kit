# Session start

Start-of-session briefing — the bookend to `wrap-up`. Reads the living handoff, the
friction-log inbox, your tracker, and live repo/CI state, then proposes **what to do
next**: candidates grouped by **urgency** and tagged `[size · model · mode]`, ending
with one recommendation.

## Resolve configuration

Read `config/dev-model.yaml` first. In this workflow:

- `<handoff>` and `<friction-log>` mean `paths.handoff` and `paths.friction_log`.
- `<engine-dir>` means `paths.engines`.
- `cheap`, `default`, and `expensive` are the neutral keys under `models.tiers`.
  Apply the current runtime's `models.runtime_mappings` value only when the runtime
  can actually select a model or effort level for that step.
- A workflow invocation means the current agent's native adapter: `/name` for the
  shipped Claude commands or `$name` for the shipped Codex skills.

## What it reads

| Source          | How                                                                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Living handoff   | `<handoff>` — latest session block + every "Next:" / "Follow-ups:" trail                                                              |
| Friction inbox   | `<friction-log>` — entries since the last "Backlog migrated" marker                                                                  |
| Tracker backlog  | your tracker's list-issues command/script — project `tracker.project_name` (open only — drop `completed`/`canceled`)                     |
| Open PRs         | `gh pr list` — anything draft / CI-red / awaiting-review (the PR-follow-through rule)                                                    |
| Working tree     | `git status --short` + `git branch --show-current` — unfinished business from last session                                              |
| CI/cron health   | your cron/CI runner's status command (adapt to your infra — e.g. a wrapper script that logs recent job outcomes)                         |
| Config drift     | your host config-apply step, if you have one (e.g. a `verify --json`-style check comparing committed config against applied host state) — drop this bullet entirely if it doesn't generalize to your setup |

### 0 · Gather (run in parallel)

Fire these together — they're independent:

- `git status --short` and `git branch --show-current`
- `gh pr list --state open --json number,title,isDraft,reviewDecision,statusCheckRollup,author --limit 20` (`author` distinguishes a **cron/automation-opened** PR from one a person opened; those are guarded out of `pr-watch` by your cron runner's job-name signal, so their bot findings get no automated follow-through and the next cockpit must adopt them — see Step 2)
- your cron/CI health command (adapt to your infra)
- your config-drift check, if you have one (parse its output for a 🔴-worthy line in Step 2)
- Read `<handoff>` (focus: the **"Latest session"** block and its `Next:` / `Follow-ups:` lines, plus the top-of-file "Last updated" trail for the active sprint)
- Read `<friction-log>` (the inbox — entries above the most-recent `## … — Backlog migrated to <tracker>` marker; everything below it is already ticketed)
- **Tracker** (optional — if the script/key fails, note the gap and continue): a field-limited list-issues call against `tracker.project_name` (id/identifier/title/url/state/priority/updated — avoid pulling full descriptions, which is what makes a naive "dump everything" call routinely overflow a tool's token limit). Discard issues whose state type is `completed`/`canceled`, and print a compact table sorted urgent(1) → low(4) with no-priority(0) last. A missing/invalid config or missing tracker credential should exit non-zero with a clear message — treat any non-zero exit as the optional-tracker gap (note it and continue) — never act on a partial payload.

### 1 · Classify each candidate

Turn the raw signals into a deduped candidate list. Each candidate gets an **urgency
bucket**, a **size**, a **model tier**, an **execution mode**, and a **source
pointer**.

**Urgency** (the grouping axis):

- 🔴 **Now** — broken or actively in-flight. A CI/cron failure on an active job that
  needs recovery; an open PR that's CI-red or has unaddressed review (opening/pushing
  a PR isn't done — watch-and-fix is the same task) — **including a cron/automation-
  opened PR** (identified by `author` in the gather) with a changes-requested decision
  or unresolved bot findings: your cron runner's job-name guard means `pr-watch`
  never watched it, so adopting it (run `pr-watch <PR#>`) is this session's job;
  uncommitted work from last session that should be finished or committed; the
  handoff's explicit current `Next:` **iff** it's the active sprint's blocking step;
  any entry your config-drift check flags — a merged config change that's inert on
  the host until applied is an **operator host-action** reminder, not a delegatable
  build candidate — render it without model/mode tags (see Step 2).
- 🟡 **Soon** — this week's clear next steps. Active-sprint follow-ups, time-bound
  items ("validate Wednesday's run"), medium-severity friction-log entries,
  started/high-priority tracker tickets.
- 🟢 **Whenever** — backlog. Low-severity friction-log entries, lower-priority tracker
  tickets, nice-to-haves.

**Size** `S / M / L` — scope/effort: `S` ≤ one small PR (~30 min); `M` a focused
single-concern PR (~an hour); `L` multi-PR or a sprint slice.

**Model tier** — the *intelligence* the work needs (orthogonal to size — a large
mechanical sweep is `L · cheap`; a one-line calibration decision is `S · expensive`).
The three tier names below are runtime-neutral. Use the current runtime's mapping
when it exposes model or reasoning-effort controls; otherwise keep the tier as
planning guidance. **Default to the middle tier** for well-specified, self-contained
work. Reserve the top tier for genuinely tough problems and the cheap tier for
purely mechanical work:

- **`cheap`** — purely mechanical / deterministic: renames, dead-code removal,
  config sweeps, applying a known one-line fix. No grounding or judgment needed.
- **`default`** — **the default tier.** Self-contained build / refactor / doc
  work with clear acceptance criteria, *including* work that must verify itself
  against live code/schema; given a precise spec it produces top-tier-grade output.
  This is the default `delegate` tier.
- **`expensive`** — reserve for the *really tough* tasks: design decisions,
  calibration / threshold choices, ambiguous or emergent scoping, security-sensitive
  changes, cross-system reasoning — anything where being wrong is expensive and hard
  to catch in review. These almost always run `inline` (expensive tier + judgment ⇒
  inline), not delegated.

**Execution mode** `inline / delegate` — *where* the work runs once you greenlight it;
the token lever (a plan, not an action — nothing launches until the operator picks one
in Step 3):

- **`delegate`** — use the current runtime's isolated-task mechanism for
  **self-contained, clearly specified work**, while the cockpit retains orchestration
  and review. Request the mapped tier only when that mechanism supports it. Drop to a
  cheap-tier delegate only for purely mechanical sweeps; an expensive-tier delegate
  is rare because high-judgment work usually benefits from live steering.
- **`inline`** — do it in this session. Right when the item is **expensive-tier**
  (high judgment), needs **live iteration / your input as it unfolds**, or is
  **exploratory** (scope emerges as you go). If you want a cheaper tier for an inline
  item, adjust the session's model or effort only when the runtime exposes that
  control; live steering matters more than the exact setting.

Rule of thumb: `self-contained + clear spec ⇒ delegate to default` (cheap-tier
only for purely mechanical sweeps); `really tough / high-judgment, or
interactive/exploratory ⇒ inline on expensive`. When in doubt, default `inline`
(no regression vs today).

**Source pointer** — every item shows where it came from so you can drill in:
`handoff`, `friction-log <date>`, a tracker ticket id, `PR #NNN`, or the job name.

**Rules:**

- **Dedup.** An item that appears in more than one source (a friction-log entry that's
  also a tracker ticket, say) is listed **once**, with the most authoritative pointer
  (tracker > handoff > inbox) and any others noted inline.
- **Don't invent work.** Only surface candidates traceable to one of the sources
  above. If a source is empty or clean, say so — a quiet bucket is a real result.
- Keep each line to one sentence of *what* + the tags + the pointer. No essays.
- **Composing an autonomous/overnight self-merge batch:** also tag each lane with its
  predicted merge class (self-merge / operator-merge — see `parallel`'s per-lane
  merge-class table) and report the split to the operator before launch — e.g. "2 will
  self-merge, 3 held for you."

### 2 · Render the briefing

```text
🧭 Session Start — <Day YYYY-MM-DD>

Where things stand
  • <branch> (<clean | N uncommitted/untracked>) · <N> open PRs · CI/cron: <all green | N failed/skipped>
  • Active sprint: <one line, from handoff top trail>
  • Last session: <one-line theme from the latest handoff block>

What to do next

🔴 Now
  • <what>   [<S/M/L> · <cheap/default/expensive> · <inline/delegate>]   <pointer>
  • N config change(s) INERT pending a host apply step — <name1>, <name2>, …   <pointer: your drift check>
🟡 Soon
  • <what>   [<S/M/L> · <model> · <mode>]   <pointer>
🟢 Whenever
  • <what>   [<S/M/L> · <model> · <mode>]   <pointer>
```

- Omit a bucket entirely if it's empty (don't print "🔴 Now: nothing"), but if **all**
  of Now+Soon are empty, say so plainly — e.g. `✅ All clear — nothing urgent or due
  this week; see 🟢 Whenever for backlog.`
- Order items within a bucket by leverage (blocking > high-value > cheap-win).
- The config-drift line only appears when your drift check reports something
  outstanding; name the affected items. A less-urgent "orphan" class of drift (config
  present with nothing applying it, or vice versa) is a separate, lower-urgency
  concern — mention it only under 🟢 Whenever if present, never conflated with the 🔴
  line above.

### 3 · Recommend one, then wait

End with a single pick and a one-line why, then **stop** — let the operator choose. Do
not auto-start the work.

```text
👉 My pick: <item>   [<S/M/L> · <model> · <inline/delegate>] — <one-line rationale: why this, now>
   <delegate ⇒ "I'll hand it to an isolated task and review the result here." | inline ⇒ "We'll run it in this session so you can steer it.">
   Want me to start it, or pick another?
```

Rationale heuristics: prefer 🔴 Now if the bucket is non-empty; otherwise the active
sprint's blocking next step; break ties toward the highest value-per-effort (small +
high-leverage).

## Notes

- **Read-only.** This skill never edits, commits, or starts work — it only reports
  and recommends. It's safe to run anytime to re-orient mid-session.
- If `<handoff>` or `<friction-log>` is over its line budget (a
  session-start tripwire may have warned), mention it as a 🟢 housekeeping item
  (`wrap-up` sweeps the handoff; the `triage-friction-log` workflow graduates the inbox) — don't
  sweep inline.
- Pairs with `wrap-up` (session end). Use `pr-watch` to action a 🔴 PR item,
  the `triage-friction-log` workflow to clear the inbox.
