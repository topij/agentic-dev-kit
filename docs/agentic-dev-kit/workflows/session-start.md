# Session start

Start-of-session briefing — the bookend to `wrap-up`. Reads the living handoff, the
friction-log inbox, your tracker, and live repo/CI state; checks anything urgent
against the narrative archives before promoting it; then proposes **what to do
next**: candidates grouped by **urgency** and tagged `[size · model · mode]`, ending
with one recommendation.

## Resolve configuration

Read `config/dev-model.yaml` first. In this workflow:

- `<handoff>` and `<friction-log>` mean `paths.handoff` and `paths.friction_log`;
  `<handoff-history>` and `<friction-log-archive>` mean `paths.handoff_history` and
  `paths.friction_log_archive`.
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
| Tracker backlog  | your tracker's list-issues command/script — project `tracker.project_name` (open only — drop `completed`/`canceled`). Pass an explicit row limit *and* select fields; see the gather for why these are two separate limits and why a full page must be treated as truncated |
| Open PRs         | `gh pr list` — anything draft / CI-red / awaiting-review (the PR-follow-through rule). Pass an explicit `--limit`; see the gather for why a full page must be treated as truncated |
| Working tree     | `git status --short` + `git branch --show-current` — unfinished business from last session                                              |
| CI/cron health   | your cron/CI runner's status command (adapt to your infra — e.g. a wrapper script that logs recent job outcomes)                         |
| Config drift     | your host config-apply step, if you have one (e.g. a `verify --json`-style check comparing committed config against applied host state) — drop this bullet entirely if it doesn't generalize to your setup |
| Narrative archives | `<handoff-history>` + `<friction-log-archive>` — deliberately **not** part of the gather and never read whole; grepped per-candidate in *Remediation check*, and only for a candidate you are about to promote to 🔴 |

### 0 · Gather (run in parallel)

Fire these together — they're independent.

**A source that fails is reported as unavailable, never as its empty value.** A
non-zero exit, a missing binary, or an absent credential returns nothing — and
nothing is indistinguishable from a genuine zero: no open PRs, no failing jobs, no
drift. Rendering the empty value turns a command that never ran into an all-clear,
which is worse than a visible gap because nothing on the briefing says to look
again.

This governs every source whose failure can pass for a benign zero. The PR list,
your cron/CI health command and your config-drift check each have a slot in
*Render the briefing* for saying so; the tracker bullet carries the rule inline
instead, and reports its gap in the briefing text rather than in a fixed field.
The two narrative-file reads are not in this set: a failed read there does not look
like good news, it looks like a missing handoff.

- `git status --short` and `git branch --show-current`
- `gh pr list --state open --json number,title,isDraft,reviewDecision,statusCheckRollup,author --limit 100`
  — **the explicit limit matters, and so does treating a full page as suspect.**
  `gh pr list` silently defaults to 30 (`--limit int … (default 30)`, verified on
  gh 2.96.0), and it reports nothing when it truncates. If exactly `--limit` rows
  come back, assume there are more and re-run higher. This list is the whole
  input to the 🔴 bucket's PR items, so a PR that falls off the end is not
  under-reported — it is invisible, while the ones above it render as if they were
  all of them. (`author` distinguishes a **cron/automation-opened** PR from one a
  person opened; those are guarded out of `pr-watch` by your cron runner's job-name
  signal, so their bot findings get no automated follow-through and the next
  cockpit must adopt them — see *Render the briefing*.)

  Note the two failure shapes are different and only one is covered above: a
  **failed** `gh pr list` returns nothing and is caught by the unavailable rule; a
  **truncated** one returns valid JSON with fewer rows than exist, which no exit
  code reveals and only the full-page check catches.
- your cron/CI health command (adapt to your infra)
- your config-drift check, if you have one (parse its output for a 🔴-worthy line in *Render the briefing*)
- Read `<handoff>` (focus: the **"Latest session"** block and its `Next:` / `Follow-ups:` lines, plus the top-of-file "Last updated" trail for the active sprint)
- Read `<friction-log>` (the inbox — entries above the most-recent `## … — Backlog migrated to <tracker>` marker; everything below it is already ticketed)
- **Tracker** (optional — if the script/key fails, note the gap and continue): a
  field-limited list-issues call against `tracker.project_name`
  (id/identifier/title/url/state/priority/updated). Discard issues whose state type is
  `completed`/`canceled`, and print a compact table sorted urgent(1) → low(4) with
  no-priority(0) last. A missing/invalid config or missing tracker credential should
  exit non-zero with a clear message — treat any non-zero exit as the optional-tracker
  gap (note it and continue) — never act on a partial payload.

  **The call has two independent limits, and using one against the other's failure
  silently loses issues.** Field selection bounds the *bytes per row*; the row limit
  bounds *how many rows*. Neither substitutes for the other:

  - **Payload overflow** — pulling full descriptions is what makes a naive "dump
    everything" call overflow a tool's token limit. The fix is to drop the body, never
    to ask for fewer issues. One measurement carries that, taken on this repo
    2026-08-03 at 137 open issues:
    `gh issue list --state open --limit 500 --json number,title,labels,state,updatedAt,url`
    piped to `wc -c` returns ~49 KB, and appending `,body` to that same call takes it
    to ~421 KB. Field selection is what makes a
    **complete** list affordable, which is why it comes first — but it bounds the
    bytes *per row*, not the total, so a backlog large enough to overflow even a
    field-limited response needs **paging**: fetch successive pages and concatenate
    them all.
    Still never by lowering the row count, which trades this loud failure for the
    silent one below.
  - **Silent truncation** — the same failure as the PR list above, and the worse of
    the two, because the response is well-formed and the exit code is zero. Pass an
    explicit limit above your real backlog (`gh issue list` defaults to **30**, and
    `gh pr list` to 30 — both verified on gh 2.96.0), then check the row count against
    **two** ceilings rather than one: your requested limit, and the backend's own
    maximum. Equalling either means assume there are more.

    A backend maximum announces itself in one of two ways, and only one is safe. It
    may **reject** the over-cap request: both tracker MCP clients reachable from this
    session do, declaring a JSON-Schema `maximum` that fails validation — Jira's
    `searchJiraIssuesUsingJql` at `maxResults` **100**, Linear's `list_issues` at
    `limit` **250**. That is the loud kind, and it is self-correcting: you learn the
    ceiling from the error. Or it may **serve the cap and say nothing**, which is the
    same well-formed, exit-zero shape as the default above.

    Either kind lands you in the same place, which is the reason to track the second
    ceiling at all: once you have requested the backend's maximum and received
    exactly that many rows, you are at both ceilings at once and cannot tell a
    complete list from a truncated one. Raising the limit is no longer available, so
    **page** — both clients above expose it (`nextPageToken`, `cursor`) — and keep
    fetching until a short page ends the data.

    **If the response states whether more remain, that answer beats every count
    above.** Row-count arithmetic is the fallback for a backend that tells you
    nothing, and it is a heuristic that fails in both directions: it cannot fire at
    all against a cap you do not know, and it raises a false alarm on a final page
    that happens to be exactly full. A `has_next_page`-style field or a non-empty
    next-page token is the backend answering the question directly, so neither
    failure applies.
    Linear's `list_issues` returns `hasNextPage` alongside its `cursor`; read it, and
    keep paging while it is true rather than until a page looks short. Verified
    2026-08-03 against a real project: at `limit: 250`, Linear's own maximum, the
    response came back `hasNextPage: true` — the ceiling-equals-count case above,
    reported outright by the backend instead of inferred.

  Reaching for the wrong one is not hypothetical: `--limit 25` was adopted **in this
  repo** as the remedy for the overflow above and carried in the handoff as "the form
  that works here", while the backlog stood at 89 open issues. Where field selection is
  unavailable entirely, paging is the only route left rather than one option among
  several — [`#143`](https://github.com/topij/agentic-dev-kit/issues/143) reports that
  of the GitHub-Issues MCP client, and is the place to confirm it against a live
  server. Shrinking the request to fit the tool is the mistake this bullet exists to
  stop, whichever limit you shrink.

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
  build candidate — render it without model/mode tags (see *Render the briefing*).
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
in *Recommend one, then wait*):

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

### 2 · Remediation check

Before promoting any candidate to 🔴, rule out that it is a **solved problem
misread as new**. Every source in the gather shows you *live* state — a symptom is
visible there while the remediation that already addressed it is not, because the
remediation is in a file the gather deliberately does not read, or behind a
tracker state that is wrong.

This is neither of the *Classify each candidate* rules. **Dedup** is one item
appearing in several
live sources; **don't invent work** is an item traceable to no source at all. Both
are about provenance across the sources you just read. This is about an item whose
*resolution* is in none of them.

Run it only against candidates you are about to promote to 🔴 — it is a filter on
that promotion, not a pass over the whole list. That is a deliberate cost bound:
the archives are large, so checking every 🟡 and 🟢 would put an archive search
behind every candidate. It follows the promotion rather than the bucket, so if
something already classified 🟡 is later raised to 🔴, it gets the check then.

- **Archived diagnosis.** `<handoff-history>` and `<friction-log-archive>` hold
  everything the archival sweeps moved out of the two live narrative files. The
  gather reads neither, by design — they grow without bound, which is the whole
  point of sweeping into them. So a problem diagnosed three months ago is
  invisible to every other step here, and its symptom is not.

  Search them **per candidate**, by job / ticket / subject name, using **your
  runtime's own file-search facility** — the subject passed as a *parameter*, the
  two archives as the scope.

  **Skip a candidate whose subject is empty or whitespace-only** rather than
  searching for it. An empty pattern matches every line of both archives, which is
  worse than finding nothing: it is a false-positive flood over exactly the files
  this step refuses to read whole.

  **This workflow deliberately ships no shell recipe for that search.** The
  subject is candidate-derived text — a ticket title, a PR title, a job name — so
  on any repo whose tracker takes issues from outside it is attacker-influenceable,
  and a parameter is the only form never parsed as syntax. Three shell recipes were
  written for this line and each was broken by a different input, the last two by
  the fix for the one before; the full account is on
  [`#241`](https://github.com/topij/agentic-dev-kit/issues/241). If a shell is the
  only route you have, read that issue first and treat building the command as its
  own problem rather than assuming a quoting rule settles it.

  A hit **locates** a record; it does not by itself establish one. Read the entry
  the hit sits in before acting on it — these are Markdown blocks, so the
  diagnosis and any residual follow-up routinely sit on lines the grep did not
  return, and a generic subject can match an unrelated older incident. Confirm the
  entry is about *this* occurrence, then: attach it as
  `previously diagnosed: <one line> [<file>:<line>]` and **drop the candidate** —
  unless the entry names a residual follow-up still outstanding, in which case that
  follow-up is the candidate and the symptom is not. Never render a diagnosed
  symptom as a fresh 🔴.

  **Scoped grep only — never read either file whole.** They are the accumulated
  output of every sweep the repo has run; on a mature repo they reach thousands of
  lines, and reading them is how a briefing that is supposed to be cheap stops
  being one.

- **A tracker item that reads resolved but is not.** When a symptom clearly
  implicates one ticket, check that ticket **live** rather than inferring from its
  absence in the gather's open-only list. A forge's automation can move an item to
  a done state on a keyword in a PR title, a commit message, or a squash
  message — whether or not the code behind it shipped, and whether or not anyone
  meant it. That is the same mechanism the closing-keyword discipline guards
  against on the write side; this is its read side. An item the tracker shows as
  done that is not actually resolved is a real candidate, and the open-only list
  is precisely where it will not appear.

  **The live lookup is not for the state — the state is the thing you are
  distrusting.** Fetch the item by id and read what it points *at*: the commit, PR,
  or check that is supposed to have resolved it, and whether its acceptance
  criteria are met in current code. A done state with nothing behind it leaves the
  candidate standing. Keep it actionable until something other than the state says
  otherwise.

### 3 · Render the briefing

```text
🧭 Session Start — <Day YYYY-MM-DD>

Where things stand
  • <branch> (<clean | N uncommitted/untracked>) · <N open PRs | PRs unavailable: reason> · CI/cron: <all green | N failed/skipped | unavailable: reason>
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
  outstanding; name the affected items. **If the check could not run, say so where
  that line would go** — "config drift: unavailable (`<reason>`)". Silence here
  otherwise means "nothing outstanding", and a check that never ran would claim it.
  A less-urgent "orphan" class of drift (config
  present with nothing applying it, or vice versa) is a separate, lower-urgency
  concern — mention it only under 🟢 Whenever if present, never conflated with the 🔴
  line above.

### 4 · Recommend one, then wait

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
