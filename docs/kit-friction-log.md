# Friction Log — agentic-dev-kit

> **Lean inbox (Principle #2 — the friction flywheel).** Friction surfaced during real use,
> recorded at session end. Single incidents route **down** to the tracker; a genuine
> multi-occurrence **pattern** graduates **up** into a rule or skill change.
>
> **This repo's tracker is GitHub Issues on itself**, so most friction is filed directly as
> issues rather than parked here — which is the routing Principle #2 prescribes, not a
> neglected inbox. Anything that appears below a graduation marker is un-graduated: not yet
> issue-shaped, or waiting for the next `triage-friction-log` sweep.
>
> Tracker board: https://github.com/topij/agentic-dev-kit/issues

## 2026-08-05

**A negated closing keyword in a heading closes the issue listed beneath it, and the
check this repo's contract calls for cannot see that shape.** Severity **H**.

`#303`'s squash message carried a section heading `## Filed, not fixed` above a list whose
first item named `#302`. GitHub paired them across a blank line, a list marker and a
backtick. That same message said in prose that the issue stays open. It was closed on
merge, and found by going to work on it.

The contract in `AGENTS.md` already forbids this — *"in any form, even negated"*. What
failed was the implementation. The sweep being run looked for a keyword and an issue
reference within a short window **on one line**, which is the shape a human writes by
accident (`fixes #302`), not the shape a document produces structurally, where a heading
governs the list under it. "Filed, not fixed" is a natural heading for precisely the case
where you are listing issues you want left open, so the failure is aimed at its own use case.

Proposed fix: a check that pairs each closing keyword with the next issue reference
*anywhere* after it, regardless of intervening markup, and requires the author to confirm
each pairing. Loud on purpose — a false positive costs a glance, a false negative silently
closes tracked work. A draft ran against the message that slipped through and flagged the
exact pairing; it then caught the same shape in a PR body before merge, and again in a
panel report. It also flags `Principle #8`, which is the acceptable cost. Not landed:
adding a mechanism inside a fix round is a measured source of later findings, and this one
wants its own change. The blast radius of the original incident was audited — every issue
that message referenced was checked, and only the one was affected.

**Building a lens's scratch copy has a second failure that looks exactly like isolation
breaking, and is not.** Severity **M**.

`rsync -a` of a linked worktree copies `__pycache__`, and pytest's cached bytecode carries
`co_filename` from wherever it was first compiled. Mutation-test tracebacks in the isolated
copy therefore print paths under the live repo and read precisely like the copy having
written there. It is cosmetic — `__file__` still resolves to the loaded source, so the right
file is under test — but it cost real time and nearly caused a valid mutation kill to be
discarded as a false result. Established by re-running with `__pycache__` excluded and
`PYTHONDONTWRITEBYTECODE=1`, in `/Users/topi/Coding/agentic-dev-kit`, which reproduced the
same failures with scratch-relative paths.

The first failure of the same step — `rsync -a` copying the `.git` **gitlink file**, so the
copy resolves back into the live repository — is recorded on `#270` rather than restated
here. Both argue the same fix: `git clone` is the safe default
for a lens scratch copy because it cannot inherit either problem, and that belongs in the
rendered contract now that `panel_prompt.py` produces it, not in a per-round hand-written
addendum. The addendum is how the gitlink instance happened — it specified rsync excludes
without `.git`, and a lens read it as the recipe.

## 2026-08-04

**`fallback-review-panel.md` never mentions `panel_prompt.py`, so a panel is run by
hand-authoring every lens prompt — the exact failure that engine exists to prevent.**
Severity **H**.

Ran seven panel rounds on PR `#289` and hand-wrote both lens prompts each round, from the
doctrine, because the doctrine's "Running it" section describes what a lens must be told and
never says anything renders it. Only afterwards did `scripts/panel_prompt.py` turn up. Its
own docstring opens with the reason it exists:

> Assemble a fallback-review-panel launch prompt instead of hand-authoring it. … **Nothing
> rendered that.** Every prompt was hand-written from the doctrine, once per lens per round,
> and `#214` records what it cost.

Established rather than assumed: `git grep panel_prompt` outside the script, its own tests,
`kit-manifest.json` and `kit_doctor.py`'s `KIT_OWNED` returns nothing. So the engine is
shipped, kit-owned and tested, and unreachable from the only document that tells you to run a
panel — which means every adopter hand-authors prompts too.

What it cost here is the failure `#214` names: an omitted contract item is **invisible**,
because a lens cannot report the absence of an instruction it never received. The three
properties the script guarantees — the contract quoted rather than restated, the base resolved
from the remote every run, and identical inputs producing an identical prompt so a round's
framing differences are deliberate — were all things I re-established by hand each round, and
the third one I simply did not have: my round-to-round prompt variance was not deliberate.

Proposed fix: `fallback-review-panel.md` "Running it" step 2 names the engine and shows the
invocation, the way `pr-watch.md` names `pr_watch.py`. Worth checking at the same time whether
`--carry-forward` is the channel the round-N prompts should have used, since this session
passed prior-round framing as hand-written prose in the lens brief instead.

**Second occurrence, same day, on PR `#294`** — every lens prompt hand-authored again, across
many more rounds than the entry above, before this was noticed. Two things that only show at
this volume, and both are arguments for the engine rather than for discipline:

- **The brief is unverified input and nothing treats it as such.** One prompt carried a
  diffstat I had never measured; a lens caught it only because it independently ran
  `git show --stat`. A rendered prompt cannot contain a figure the author invented.
- **Round-to-round framing drift is invisible and load-bearing.** Later rounds aimed lenses
  at the previous round's defect shape, which is useful — but hand-writing it means no round
  can be compared with another, and "this round found less" is uninterpretable when the brief
  also changed. `--carry-forward` exists for exactly this.

The panel also wrote into the live checkout twice on this PR, by routes that differ —
`cp -R` of a linked worktree (`#270`'s third occurrence) and, separately, a cwd that resets
to the repo root between tool calls (its fourth). The fourth comment calls that cwd route a
new sub-mechanism; `#270`'s **first** comment already named a cwd reset as a proximate
cause, so what is new there is the route reaching `init.sh`, not the observation. Both are on `#270`, with a cockpit before/after baseline as the
proposed control. That two distinct routes reached the same damage is itself the argument
for a rendered prompt: a control stated once in an engine, rather than remembered per round
per lens.

## 2026-08-04 — `/adopt`'s guard could not be verified by anything the repo runs

Severity **H**. Not a workflow bug; a gap in what the kit can check.

PR `#294` put a safety-critical guard into `.claude/commands/adopt.md` — shell that decided
whether `init.sh` would overwrite an adopter's file. **`make test` passes in full without
executing a line of it.** No test, no linter, no CI covers a fenced block in a workflow doc,
and the defects found there were each real: a locale-dependent marker match, a scratch path
that evaporated between blocks, an unscoped `grep` that resolved a decoy path, a BSD-only
`mktemp` that silently built an empty-tree probe on Linux.

Every one was found by a human or a lens *running the snippet by hand*. That is not a
review-thoroughness problem — it is that the kit ships prose containing executable payloads
and has no way to execute them.

Proposed fix, smallest first: a check that **extracts fenced shell blocks from
`.claude/commands/` and `docs/agentic-dev-kit/` and syntax-checks each with the shell its
fence names** — `sh -n` for ```` ```sh ````, `bash -n` for ```` ```bash ```` — would have
caught the portability and quoting defects, though not the semantic ones. Matching the
checker to the fence matters: `dash -n` rejects a bash array with
`Syntax error: "(" unexpected` while `bash -n` accepts it, so checking every block with
`sh -n` would fail valid `bash` fences on a dash-based CI and pass them on macOS, where
`/bin/sh` is bash in POSIX mode. Both reproduced with `dash -n` and `bash -n` in `/Users/topi/Coding/agentic-dev-kit`. The durable
answer is the one `#294` reached by exhaustion: a predicate an engine owns is never restated
in a document — see `#297`.

## 2026-08-03 — Backlog migrated to GitHub Issues (#250–#256)

Ninth sweep, LLM-only mode ([#6](https://github.com/topij/agentic-dev-kit/issues/6) still not
vendored). **Fifteen entries in, fifteen accounted for:** seven new issues
([#250](https://github.com/topij/agentic-dev-kit/issues/250)–[#256](https://github.com/topij/agentic-dev-kit/issues/256)),
five occurrence comments (`#32`, `#47`, `#71`, `#205`, `#246`), and two entries already tagged
`#198` that route nowhere. All twelve writes were re-read from the tracker after landing per
`#138` — compared **by body**, with every commented issue confirmed still open afterwards.

**Approval.** The operator replied `lgtm` in the Slack DM thread (channel `D083840DP7B`, parent
ts `1785731335.010039`) — a bulk approve of all twelve, with nothing declined.

**Frozen inbox:** 16,413 bytes, `sha256 4d731234…`, reproducing from
`git show a447957:docs/kit-friction-log.md | tail -n +14 | shasum -a 256` — run in this session,
digest matched. The current inbox was byte-identical to it at finalize, so every block swept and
nothing was held back.

Reading the tracker before drafting changed three routings, two of them substantively; the
routing table and what this sweep does **not** establish are on the PR. Swept entries are
verbatim in the archive under `Graduated 2026-08-03`.
