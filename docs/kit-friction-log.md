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

## 2026-08-06 — the panel found the cockpit's own mutation harness, and it was the unsafe shape

Severity **M**. Not filed: `#326` already owns the class and now carries this as an occurrence
comment. Recorded here because of what it says about *how* it was found.

The cockpit needed to mutation-test two new tests whose subject was a workflow document. It
deliberately avoided `git checkout --` to revert, **because `#254`/`#326` say that is
destructive against a file holding uncommitted work** — which this one was. It used a
backup-by-copy and a `trap restore EXIT INT TERM` instead, and mutated the file **in the live
checkout**.

An adversarial review lens, reviewing the *PR*, found the harness lying in the shared scratch
root and flagged it unprompted:

> That writes into the tree I was handed, guarded only by a trap — not an isolated copy — and
> a trap doesn't survive `SIGKILL`/sandbox crash.

**The interesting part is that the cockpit was actively thinking about the adjacent hazard and
still reached for the wrong shape.** It avoided the route the tickets name and invented a
different unsafe one. That suggests the rule wants to be *"do not mutate the live tree"* rather
than *"revert safely"* — a rule about reverting invites better reverting. Both lenses mutate
clones, so the doctrine already says this for lenses; nothing says it for the cockpit, which is
`#325`'s gap.

No harm this time, and the reason is luck rather than process: the tree ended clean, and both
lenses independently reproduced every mutation kill in their own clones, so no claim depended
on the unsafe run.

## 2026-08-06 — a third session in a row where the review bot's quota shaped the work

Severity **M**. The entry below says this should graduate at the next triage sweep rather than
wait for a further occurrence, and this is that further occurrence — so the graduation is now
overdue rather than pending.

New information, and it is the useful kind: **the quota refilled mid-PR and the bot reviewed
after all.** It was quota-blocked when PR `#337` opened, so the fallback panel carried round 1;
by round 2 it had recovered and reviewed that head, raising six findings the panel had not.
Four were pre-existing defects in a document neither the panel nor any check had reason to look
at.

That changes the shape of the decision the entry below frames. The options were stated as
accept the quota / reconfigure the trigger / pay, with the panel carrying the overflow. What
this session shows is that the bot and the panel **found disjoint things** — the panel found
two regressions the bot did not, and the bot found four pre-existing gaps the panel did not —
so treating the panel as a *substitute* undersells both. Worth weighing at triage: the question
may not be "how do we always have the bot" but "what does each actually cover", which affects
whether paying is the right answer at all.

Still an operator decision and still not a kit change.

## 2026-08-06 — second occurrence of the entry below

**The bot was rate limited again, on a second consecutive session, and this time it went
down *mid-PR*.** Severity **M**. Recorded here rather than filed because it sharpens the
entry below rather than adding a new claim; the graduating shape has not changed.

CodeRabbit reviewed PR `#328` at `4576f40` and raised three findings. The fixes for **its
own findings** moved the head, and it was rate limited by the time that head existed — so
the sha that merged carried only the fallback panel's review. That is the entry below's
"one review of a superseded sha, then nothing", reproduced without a batch: one PR, one
fix round.

**The open question below is now answered, and by the bot rather than by inference.** That
entry listed three candidates — a rate-limit tier question, a batch-concurrency effect (three
lanes opening PRs within the hour), or a bad day — and said a second occurrence would separate
them. On the wrap-up PR the bot stated the cause itself:

> **Review limit reached.** `@topij`, you've reached your PR review limit, so we couldn't
> start this review. **Next review available in: 52 minutes.** You've used all free OSS
> reviews for now.

So it is the **tier**: a free-OSS quota that refills on a timer, not a batch effect and not
chance. Two independent supports — this session opened a *single* PR and still exhausted it,
so sequencing is not the driver.

That changes the graduating shape. "Record when the fallback carried review, so the rate is
visible" was written when the rate was the unknown; the unknown now is **what the quota
actually is and whether the work fits inside it**, which observability alone does not answer.
The bot's own suggestions (pause incremental auto-reviews, label-based opt-in, request review
when the PR is ready) are configuration this repo could adopt without an account change —
worth weighing against a paid tier rather than assuming either.

Still not filed, deliberately: the remedy is now clearly an **operator decision** (accept the
quota and let the panel carry the overflow, change the bot's trigger configuration, or pay),
and none of those is a kit change. The value of this entry is that the decision is now
informed. It should graduate at the next triage sweep rather than wait for a third occurrence,
since waiting can no longer teach anything new.

## 2026-08-06

**The configured review bot carried none of the merged review across a batch, so every lane
paid for a manual fallback panel.** Severity **M**. Parked here rather than filed,
deliberately — see the last paragraph.

Three lanes were **launched**; two opened PRs (`#315`, `#317`) and the third never started.
Both PRs carried `Review rate limited` on the CodeRabbit status check and `review limit
reached` in comments, and both ran the two-lens fallback panel.

**Checked rather than assumed, because the loose version was wrong.**
`gh api repos/topij/agentic-dev-kit/pulls/<n>/reviews` reports one CodeRabbit review on
`#315`, against `46ebd9e` — that PR's **first** commit, not the head that merged — and none
on `#317`. So this was not "no bot review": it was one review of a superseded sha, then
nothing. A bot that never ran and a bot whose output aged out under a fix round are different
problems, and the second is `#305`'s.

**The marker is not the inverse of coverage.** On the wrap-up PR carrying this entry,
`pr_watch` reported an `unavailable` hit (`review limit reached`) **and**
`coverage … covers_head: true` in the same poll. `unavailable` reports that wording appeared,
not that review was absent — `covers_head` is what the merge gate actually reads, so nothing
is currently wrong, but the name promises more than it checks.

**No engine misbehaved, which is most of why this is not a ticket.** Both surfaces
`unavailable_markers` covers fired (the `#23` case), the fallback ran, a limited bot was an
action signal rather than a waiver per Principle #5, and the gate still demanded a receipt
bound to head.

What is new is **frequency**: this was the session's condition rather than one PR's bad luck,
so the panel became the review path instead of the exception. It has a cost the kit has
measured before (`review.fallback_panel`'s comment in `config/dev-model.yaml`) and no
observability — nothing records how often the fallback carried review, so "the bot is usually
up" is an assumption no command can check.

Not filed because one occurrence does not distinguish the candidates: a rate-limit tier
question (an account matter, not a kit one), a batch-concurrency effect (three lanes opening
PRs within the hour may be what exhausts the quota, making staggering the cheap answer), or a
bad day. A second occurrence would separate them, which is what this entry exists to make
recognisable. The graduating shape is probably *"record when the fallback carried review, so
the rate is visible"* rather than anything about the bot.

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
