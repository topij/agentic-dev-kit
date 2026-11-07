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
- `review.safety_critical_paths` — optional list of the paths whose changes get the
  risk tier in [`lite-review.md`](lite-review.md): a fresh-context review and the
  operator's go-ahead before the commit.
- `vcs.protected_branch` — optional: the branch that takes changes only through pull
  requests. The lite `wrap-up` then commits on a session branch and opens the pull
  request; absent, it commits to the branch checked out.

The lite `wrap-up` reads `vcs.protected_branch` from both copies of the config, and
refuses to start when either copy holds a key outside the lite config schema, or the
two name different branches. Its *Read the configuration* lists the schema. Check both
copies the same way here: the committed one by the risk tier's read below, and the
working tree's file. Report each such key, or the two branches, as a 🔴 Now item to
fix by the way out that section names. When only one copy names a protected branch,
say so.

A missing config file, an unreadable `<handoff>` or `<friction-log>`, or a missing
`paths` key is a hard stop: name what is missing and do not render a briefing.

The risk tier is a declared capability, and the briefing always prints its line.
Read the key as `lite-review.md`'s *Risk tier* does, from the committed config, and
judge it by the rules there:

- `Risk tier: configured — <the declared paths>` when it is a usable list;
- `Risk tier: not configured (lite)` when it is absent, null or an empty list, which
  leaves every change to the same-context review;
- `Risk tier: unreadable (<reason>)` when it is anything else, or when Git cannot
  show the committed config. Add a 🔴 Now item to fix it, by the way out
  `lite-review.md`'s *Risk tier* names: the lite `wrap-up` refuses to start while it
  is unreadable.

When the working tree's config declares a different list, say so on that line: the
change to it will itself take the tier.

## Sources

| Source | How | When it cannot be read |
|---|---|---|
| Living plan | read `<handoff>` whole | hard stop |
| Friction inbox | read `<friction-log>` whole | hard stop |
| Working tree | `git status --short`, and `git symbolic-ref --short -q HEAD`; if that prints nothing, `git rev-parse --verify HEAD` and report `DETACHED at <sha>` | hard stop |
| Recent commits | `git log --oneline -15` | report `recent commits: unavailable (<reason>)` |
| Repository sources | each read the repository's `AGENTS.md` names for `session-start`, as it says to run it | report `<source>: unavailable (<reason>)` |
| Forge, tracker, CI, scratch | not part of this profile, unless a repository source reads one | report `not installed (lite)` |

**Repository sources** are the reads a repository adds to this workflow: a deploy-state
check, open pull requests across its service repositories, its roadmap's current phase.
They live in a section of the repository's `AGENTS.md` that names this workflow, not in
this kit-owned doc. Each counts as a source above: a candidate traced to one is not
invented work, and the rule below applies to it. When a repository source reads the
forge, tracker or CI, its result replaces `not installed (lite)` for that one.

<!-- lite:begin source-failure -->
**A source that fails is reported as unavailable, never as its empty value.** A
non-zero exit, a missing binary, or an absent credential returns nothing — and
nothing is indistinguishable from a genuine zero: no open PRs, no failing jobs, no
drift. Rendering the empty value turns a command that never ran into an all-clear,
which is worse than a visible gap because nothing on the briefing says to look
again.
<!-- lite:end source-failure -->

**A query narrower than intended fails the same way, without an error.** A filter the
server applies can match less than its author meant: `gh issue list --label P1,P2`
matches only issues carrying *both* labels, so it exits 0 with nothing while P2 issues
are open. Fetch wide and filter locally, and print the filtered count beside
the total it came from (`P1/P2: 0 of 14 open`), so an over-narrow filter shows.

`not installed (lite)` is a third answer, distinct from both: the source does not
exist in this repository by choice. Print it rather than leaving the line out, so the
briefing shows what the full profile would add. When a repository grows CI, a tracker
it wants driven, or parallel agents, that line is the prompt to consider the full
profile.

## Classify

Turn what you read into a short list of candidates. Each gets an urgency, a size and
a pointer to where it came from (`plan:<section>`, `friction-log <date>`, or `commit
<sha>`).

- 🔴 **Now** — uncommitted or half-finished work from the last session; a next step the
  plan marks as blocking; a friction entry that says it blocks work; a repository
  source's result its `AGENTS.md` section marks as urgent.
- 🟡 **Soon** — the plan's clear next steps; high- and medium-severity friction entries.
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
  • <each repository source>: <its result | unavailable: reason>
  • Forge / tracker / CI / scratch: <not installed (lite), for each no repository source reads>
  • Risk tier: <configured — paths | not configured (lite) | unreadable: reason>

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
