# Session start (lite)

Start-of-session briefing for a repository on the kit's **lite profile**: one operator
and an agent, a living plan, a friction inbox, and no engines, forge loop, tracker
integration or CI health read. It reads the plan and the inbox, looks at the working
tree and recent commits, and proposes what to do next. It writes nothing.

The full profile's version is the kit's `session-start` workflow, which a lite install
does not carry. The clauses between `lite:begin` and `lite:end` markers are shared with
it word for word, and a kit test keeps them so; change one in the full doc and the lite
doc together.

## Read the configuration

Read `config/dev-model.yaml` directly; a lite repository has no loader. Use:

- `profile` — `lite`. Any other value, or no value, means this is not a lite
  repository and this workflow does not apply: stop and say so to the operator.
- `paths.handoff` — the living plan, `<handoff>`. It may be a file the repository
  already kept before the kit, such as `docs/plan.md`.
- `paths.friction_log` — the friction inbox, `<friction-log>`.
- `friction.down_route` — optional free text saying where a fully explained finding
  goes in this repository (for example "fix it now and log it in `docs/FIXLOG.md`").

A missing config file, an unreadable `<handoff>` or `<friction-log>`, or a missing
`paths` key is a hard stop: name what is missing and do not render a briefing.

## Sources

| Source | How | When it cannot be read |
|---|---|---|
| Living plan | read `<handoff>` whole | hard stop |
| Friction inbox | read `<friction-log>` whole | hard stop |
| Working tree | `git status --short`, and `git symbolic-ref --short -q HEAD`; if that prints nothing, `git rev-parse --verify HEAD` and report `DETACHED at <sha>` | hard stop |
| Recent commits | `git log --oneline -15` | report `recent commits: unavailable (<reason>)` |
| Forge, tracker, CI, scratch | not part of this profile | report `not installed (lite)` |

<!-- lite:begin source-failure -->
**A source that fails is reported as unavailable, never as its empty value.** A
non-zero exit, a missing binary, or an absent credential returns nothing — and
nothing is indistinguishable from a genuine zero: no open PRs, no failing jobs, no
drift. Rendering the empty value turns a command that never ran into an all-clear,
which is worse than a visible gap because nothing on the briefing says to look
again.
<!-- lite:end source-failure -->

`not installed (lite)` is a third answer, distinct from both: the source does not
exist in this repository by choice. Print it rather than leaving the line out, so the
briefing shows what the full profile would add. When a repository grows a remote, CI
or parallel agents, that line is the prompt to consider the full profile.

## Classify

Turn what you read into a short list of candidates. Each gets an urgency, a size and
a pointer to where it came from (`plan:<section>`, `friction-log <date>`, or `commit
<sha>`).

- 🔴 **Now** — uncommitted or half-finished work from the last session; a next step the
  plan marks as blocking.
- 🟡 **Soon** — the plan's clear next steps; medium-severity friction entries.
- 🟢 **Whenever** — the rest of the plan's backlog; low-severity friction entries;
  housekeeping, such as a plan line that names work the recent commits show is done.

Size is `S` (one small change), `M` (a focused change of about an hour) or `L`
(several sessions).

<!-- lite:begin dont-invent-work -->
- **Don't invent work.** Only surface candidates traceable to one of the sources
  above. If a source is empty or clean, say so — a quiet bucket is a real result.
<!-- lite:end dont-invent-work -->
- **The most recent commit is not an instruction.** It says what just happened; the
  plan says what is next.
- One sentence per candidate. No essays.

## Render

```text
🧭 Session Start (lite) — <Day YYYY-MM-DD>

Where things stand
  • <branch | DETACHED at <sha>> (<clean | N uncommitted/untracked>)
  • Recent commits: <one line | unavailable: reason>
  • Forge / tracker / CI / scratch: not installed (lite)

What to do next
🔴 Now
  • <what>   [<S/M/L>]   <pointer>
🟡 Soon
  • <what>   [<S/M/L>]   <pointer>
🟢 Whenever
  • <what>   [<S/M/L>]   <pointer>
```

Omit an empty bucket. If Now and Soon are both empty, say so plainly.

## Recommend one, then wait

End with one pick and a one-line reason. When the operator named a task in the
invocation, that is the pick; a 🔴 item stays in the briefing beside it. Otherwise
prefer 🔴 Now, then the plan's next step, then the smallest high-value item.

```text
👉 My pick: <item>   [<S/M/L>] — <why this, now>
   Want me to start it, or pick another?
```

Then stop and let the operator choose. Do not start the work.
